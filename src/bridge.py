"""Experimental Bluetooth -> virtual Switch Pro bridge. GPL-3.0-or-later."""
import argparse
import asyncio
import contextlib
import dataclasses
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import socket
import struct
import sys
import time

from bleak import BleakClient, BleakScanner
from protocol import (BUTTONS, WRITE, RESPONSE, INPUT, RUMBLE, INIT, SILENT,
    Calibration, Sample, command, is_pro2, remap_buttons, switch_report,
    decode_switch_rumble, rumble_packet, vibration_frame)
from dsu import DSU
from native_pro import NativeProServer
from hd_rumble import HDRumble, packet_frames
from configuration import load_config,update_config
from ble_connection import controller_connection,request_throughput,release_request
from version import __version__

ROOT = Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent.parent
LOG = logging.getLogger('ProCon2Bridge')
BUS = '8-32'
USBIP = Path(os.environ.get('ProgramFiles',r'C:\Program Files'))/'USBip'/'usbip.exe'

async def run_usbip(*args):
    proc = await asyncio.create_subprocess_exec(str(USBIP),*args,
        stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,
        creationflags=0x08000000 if os.name=='nt' else 0)
    try:
        out,err = await asyncio.wait_for(proc.communicate(),12)
    except BaseException:
        with contextlib.suppress(ProcessLookupError): proc.kill()
        await proc.wait()
        raise
    return proc.returncode,(out+err).decode(errors='replace').strip()

async def detach_own_device(port):
    code,output = await run_usbip('port')
    if code: return
    # Detach only our exact endpoint and bus, never another USB/IP user's device.
    for block in re.split(r'(?=Port\s+\d+:)',output,flags=re.I):
        if re.search(rf'usbip://127\.0\.0\.1:{port}/{BUS}(?:\s|$)',block):
            match = re.search(r'Port\s+(\d+):',block,re.I)
            if match:
                await run_usbip('detach','-p',str(int(match[1])))

class Bridge:
    def __init__(self,cfg,options,config_path):
        self.cfg,self.options,self.config_path = cfg,options,config_path
        self.loop = asyncio.get_running_loop()
        self.server = None
        self.dsu = DSU()
        self.hd = HDRumble(lambda:self.state=='connected',cfg['rumble_strength'])
        self.hd_was_active = False
        self.client = None
        self.calibrations = [Calibration(),Calibration()]
        self.response = asyncio.Queue()
        self.lock = asyncio.Lock()
        self.disconnected = asyncio.Event()
        self.sequence = 0
        self.frames = (SILENT,SILENT)
        self.rumble_at = 0
        self.rumble_pending = False
        self.last_input = 0
        self.count = self.invalid = 0
        self.sample = Sample()
        self.raw_sample = Sample()
        self.state = 'starting'
        self.address = ''
        self.cal_samples = []
        self.calibration_done = not options.calibrate
        self.observed_buttons = 0
        self.accel_min = self.accel_max = None
        self.gyro_min = self.gyro_max = None
        self.settled = False
        self.settle_until = 0
        self.throughput_request = None
        self.ever_connected = False
        self.config_stamp = None
        self.background_tasks = set()

    def status(self):
        data = dict(version=__version__,state=self.state,address=self.address,report_count=self.count,
            invalid_reports=self.invalid,seconds_since_input=round(time.monotonic()-self.last_input,3) if self.last_input else None,
            buttons=[k for k,v in BUTTONS.items() if self.raw_sample.buttons&v],
            mapped_buttons=[k for k,v in BUTTONS.items() if self.sample.buttons&v and k not in ('GL','GR','C')],
            button_mapping=self.cfg['button_mapping'],
            observed_buttons=[k for k,v in BUTTONS.items() if self.observed_buttons&v],
            accel_range=[self.accel_min,self.accel_max],gyro_range=[self.gyro_min,self.gyro_max],
            sample=dataclasses.asdict(self.raw_sample),virtual_output=bool(self.server),
            motion_clients=len(self.dsu.clients),hd_active=self.hd.active(),hd_packets=self.hd.accepted,
            hd_invalid=self.hd.invalid,updated_at=time.strftime('%Y-%m-%dT%H:%M:%S%z'))
        temp = ROOT/'status.tmp'
        temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        temp.replace(ROOT/'status.json')

    async def send(self,cmd,sub,data=b''):
        async with self.lock:
            while not self.response.empty(): self.response.get_nowait()
            await self.client.write_gatt_char(WRITE,command(cmd,sub,data),response=False)
            async with asyncio.timeout(3):
                while True:
                    response = await self.response.get()
                    if len(response)>=8 and response[0]==cmd and response[1]==1:
                        return response[8:]

    async def memory(self,address,length=11):
        data = await self.send(2,4,bytes([length,0x7e,0,0])+struct.pack('<I',address))
        if len(data)<8+length or data[0]!=length or struct.unpack_from('<I',data,4)[0]!=address:
            raise RuntimeError('invalid controller memory response')
        return data[8:8+length]

    async def initialize(self):
        try:
            self.throughput_request = await request_throughput(self.client)
        except Exception as error:
            LOG.info('Bluetooth throughput preference unavailable: %s',error)
        await self.client.start_notify(RESPONSE,lambda _,d:self.response.put_nowait(bytes(d)))
        for cmd,sub,data in INIT:
            await self.send(cmd,sub,bytes.fromhex(data))
        info = await self.memory(0x13000,64)
        vid,pid = struct.unpack_from('<HH',info,18)
        if (vid,pid)!=(0x57e,0x2069): raise RuntimeError('unexpected controller identity')
        for i,(user,factory) in enumerate(((0x1fc042,0x130a8),(0x1fc062,0x130e8))):
            try:
                cal = await self.memory(user)
                if cal[:3]==b'\xff'*3: cal = await self.memory(factory)
                self.calibrations[i] = Calibration.parse(cal)
            except (RuntimeError,TimeoutError) as error:
                LOG.warning('Stick %d factory calibration unavailable: %s',i,error)
        host = self.cfg.get('host_mac','auto')
        if host=='auto':
            from winrt.windows.devices.bluetooth import BluetoothAdapter
            adapter = await BluetoothAdapter.get_default_async()
            if adapter is None: raise RuntimeError('Bluetooth adapter unavailable')
            host = adapter.bluetooth_address
        elif isinstance(host,str): host = int(host.replace(':','').replace('-',''),16)
        mac = host.to_bytes(6,'little')
        for sub,data in ((1,b'\0\x02'+mac+mac),
            (4,bytes.fromhex('00eabd4713893542c679ee07f2532c6c31')),
            (2,bytes.fromhex('0040b08a5fcd1f9b41125cacc63f38a073')),(3,b'\0')):
            await self.send(21,sub,data)
        self.settled = False
        self.settle_until = time.monotonic()+1
        session=self.client
        await session.start_notify(INPUT,lambda sender,data:self.input(sender,data)
            if self.client is session and not self.disconnected.is_set() else None)
        LOG.info('Bluetooth initialized; sticks=%s',self.calibrations)

    def input(self,_,data):
        try: sample = Sample.parse(data,self.calibrations,self.cfg['deadzone'])
        except ValueError:
            self.invalid += 1; return
        now = time.monotonic()
        self.last_input,self.raw_sample = now,sample
        self.count += 1
        self.observed_buttons |= sample.buttons
        for name in ('accel','gyro'):
            values = list(getattr(sample,name))
            low,high = getattr(self,name+'_min'),getattr(self,name+'_max')
            setattr(self,name+'_min',[min(a,b) for a,b in zip(low,values)] if low else values)
            setattr(self,name+'_max',[max(a,b) for a,b in zip(high,values)] if high else values)
        if not self.settled:
            self.settled = sample.buttons==0 or now>=self.settle_until
            if not self.settled: return
        if not self.calibration_done:
            # Save bias only after 160 consecutive still samples (~2.4s at 67Hz).
            if sample.buttons or math_norm(sample.gyro)>150 or not 3600<math_norm(sample.accel)<4600:
                self.cal_samples.clear()
            else: self.cal_samples.append(sample.gyro)
            if len(self.cal_samples)>=160:
                self.cfg['gyro_bias'] = [sum(v[i] for v in self.cal_samples)/len(self.cal_samples) for i in range(3)]
                self.cfg['gyro_calibrated'] = True
                task=asyncio.create_task(self.save_calibration())
                self.background_tasks.add(task);task.add_done_callback(self.background_tasks.discard)
                self.calibration_done = True
                LOG.info('Saved still gyro bias: %s',self.cfg['gyro_bias'])
        self.sample = dataclasses.replace(sample,buttons=remap_buttons(sample.buttons,self.cfg['button_mapping']))
        if self.server: self.server.update_state(switch_report(self.sample,self.cfg['gyro_bias'],self.cfg['gyro_scale']))
        self.dsu.connected = True
        self.dsu.publish(self.sample,self.cfg['gyro_bias'],self.cfg['gyro_scale'])

    def feedback(self,data):
        if not data or data[0]==0:
            frames = (SILENT,SILENT)
        elif data[0] in (1,16) and len(data)>=10:
            frames = tuple(decode_switch_rumble(data[i:i+4],self.cfg['rumble_strength']) for i in (2,6))
        else: return
        self.loop.call_soon_threadsafe(self.set_rumble,frames)

    def set_rumble(self,frames):
        if self.hd.active(): return
        self.frames,self.rumble_at,self.rumble_pending = frames,time.monotonic(),True

    async def write_rumble(self,frames):
        await self.write_packet(rumble_packet(self.sequence,*frames))

    async def write_packet(self,packet):
        await asyncio.wait_for(self.client.write_gatt_char(RUMBLE,packet,response=False),.25)
        self.sequence += 1

    async def save_calibration(self):
        try:
            await asyncio.to_thread(update_config,self.config_path,
                {'gyro_bias':self.cfg['gyro_bias'],'gyro_calibrated':True})
        except Exception: LOG.exception('Could not save gyro calibration')

    def release_controls(self):
        self.sample=Sample();self.raw_sample=Sample();self.last_input=0
        self.dsu.connected=False
        if self.server: self.server.update_state(switch_report(Sample()))

    def controller_disconnected(self,client):
        if self.client is client:
            self.state='reconnecting';self.release_controls();self.disconnected.set()

    async def maintenance(self):
        last_status=last_config=0
        while True:
            await asyncio.sleep(.1)
            now=time.monotonic()
            if self.state=='connected' and self.last_input and now-self.last_input>2:
                LOG.warning('Input timeout; releasing controls and reconnecting')
                self.release_controls();self.disconnected.set()
            if now-last_config>.5:
                last_config=now
                try:
                    stamp=self.config_path.stat().st_mtime_ns
                    if stamp!=self.config_stamp:
                        self.config_stamp=stamp
                        cfg=await asyncio.to_thread(load_config,self.config_path)
                        if cfg['button_mapping']!=self.cfg['button_mapping']:
                            self.cfg['button_mapping']=cfg['button_mapping']
                            LOG.info('Applied updated button mappings')
                except (OSError,ValueError): LOG.warning('Invalid config update; keeping active mappings',exc_info=True)
            if now-last_status>1:
                try: self.status()
                except OSError: LOG.warning('Cannot update local status file',exc_info=True)
                last_status=now

    async def ticks(self):
        deadline=time.monotonic()
        while True:
            deadline=max(deadline+.015,time.monotonic())
            await asyncio.sleep(max(0,deadline-time.monotonic()))
            now = time.monotonic()
            if self.client and self.client.is_connected and self.state=='connected':
                hd_active=self.hd.active()
                if hd_active or self.hd_was_active:
                    try:
                        await self.write_packet(packet_frames(self.sequence,self.hd.frames(now)))
                    except Exception as error:
                        LOG.warning('HD haptics write failed: %s',error);self.release_controls();self.disconnected.set()
                    self.frames=(SILENT,SILENT);self.rumble_pending=False
                elif self.rumble_pending or self.frames!=(SILENT,SILENT):
                    if now-self.rumble_at>.2: self.frames = (SILENT,SILENT)
                    try: await self.write_rumble(self.frames)
                    except Exception as error:
                        LOG.warning('Haptics write failed: %s',error)
                        self.release_controls()
                        self.disconnected.set()
                    self.rumble_pending = False
                self.hd_was_active=hd_active

    async def run(self):
        if not self.options.monitor:
            if not USBIP.is_file(): raise RuntimeError('USB/IP driver missing. Run INSTALL-DRIVER.cmd once, then START.cmd.')
            self.server = NativeProServer(host='127.0.0.1',port=self.cfg['usbip_port'],
                bus_id=BUS,mac_address='02:50:43:32:00:01',on_rumble_callback=self.feedback)
            self.server.start()
            code,output = await run_usbip('-t',str(self.cfg['usbip_port']),'attach','-r','127.0.0.1','-b',BUS)
            if code: raise RuntimeError(f'Virtual Switch Pro attach failed ({code}): {output}')
            LOG.info('Virtual Switch Pro attached: %s',output)
        transport,_ = await self.loop.create_datagram_endpoint(lambda:self.dsu,
            local_addr=('127.0.0.1',self.cfg['dsu_port']))
        hd_transport,_ = await self.loop.create_datagram_endpoint(lambda:self.hd,
            local_addr=('127.0.0.1',26761))
        ticker = asyncio.create_task(self.ticks())
        maintainer = asyncio.create_task(self.maintenance())
        try:
            while True:
                self.state = 'scanning'; self.status()
                LOG.info('Waiting for Pro Controller 2. Press a button, or hold SYNC for first pairing.')
                device = await BleakScanner.find_device_by_filter(lambda d,a:is_pro2(d,a) and
                    (not self.cfg['device_address'] or d.address.upper()==self.cfg['device_address'].upper()),timeout=20)
                if device is None: continue
                self.address = device.address
                self.state = 'connecting'; self.disconnected.clear(); self.status()
                try:
                    async with controller_connection(device,BleakClient,
                        self.controller_disconnected,
                        cached=self.ever_connected) as client:
                        self.client = client
                        await asyncio.wait_for(self.initialize(),50)
                        self.state = 'connected'; self.last_input = time.monotonic(); self.status()
                        self.ever_connected=True
                        LOG.info('Connected %s, native input + gyro ready',self.address)
                        if self.options.test_rumble:
                            LOG.info('Testing left then right actuator, 0.5s each')
                            frame = vibration_frame(lf=500,hf=280)
                            try:
                                for frames in ((frame,SILENT),(SILENT,frame)):
                                    end = time.monotonic()+.5
                                    while time.monotonic()<end:
                                        await self.write_rumble(frames)
                                        await asyncio.sleep(.015)
                            finally:
                                await self.write_rumble((SILENT,SILENT))
                        await self.disconnected.wait()
                except asyncio.CancelledError:
                    if asyncio.current_task().cancelling(): raise
                    LOG.warning('Windows cancelled GATT discovery; retrying')
                except Exception:
                    LOG.exception('Bluetooth connection failed; retrying')
                finally:
                    self.state='reconnecting'
                    release_request(self.throughput_request);self.throughput_request=None
                    self.client = None; self.frames = (SILENT,SILENT)
                    self.rumble_pending=False;self.rumble_at=0;self.hd_was_active=False
                    self.hd.reset()
                    self.release_controls()
                await asyncio.sleep(2)
        finally:
            ticker.cancel();maintainer.cancel()
            with contextlib.suppress(asyncio.CancelledError): await ticker
            with contextlib.suppress(asyncio.CancelledError): await maintainer
            transport.close()
            hd_transport.close()

    async def close(self):
        if self.client and self.client.is_connected:
            with contextlib.suppress(Exception): await self.write_rumble((SILENT,SILENT))
        if self.server:
            with contextlib.suppress(Exception): await detach_own_device(self.cfg['usbip_port'])
            self.server.stop()
        self.dsu.connected = False
        if self.background_tasks: await asyncio.gather(*self.background_tasks,return_exceptions=True)
        self.state = 'stopped'; self.status()

def math_norm(values): return sum(v*v for v in values)**.5

async def main(options):
    cfg_path = ROOT/'config.json'
    cfg=load_config(cfg_path)
    options.calibrate=options.calibrate or not cfg.get('gyro_calibrated',any(cfg['gyro_bias']))
    if options.calibrate: LOG.info('Keep the controller flat and still for initial gyro calibration after connection.')
    bridge = Bridge(cfg,options,cfg_path)
    # Exclusive loopback listener prevents two copies from fighting over the radio/device.
    stop = asyncio.Event()
    async def control(reader,writer):
        try:
            data = await asyncio.wait_for(reader.read(16),1)
            if data==b'stop\n':
                stop.set(); writer.write(b'OK\n'); await writer.drain()
        finally:
            writer.close()
    guard = await asyncio.start_server(control,'127.0.0.1',26759)
    running = asyncio.create_task(bridge.run())
    stopping = asyncio.create_task(stop.wait())
    try:
        done,_ = await asyncio.wait((running,stopping),timeout=options.duration or None,
            return_when=asyncio.FIRST_COMPLETED)
        if running in done: await running
    finally:
        running.cancel(); stopping.cancel()
        with contextlib.suppress(asyncio.CancelledError): await running
        with contextlib.suppress(asyncio.CancelledError): await stopping
        await bridge.close()
        guard.close(); await guard.wait_closed()

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='ProCon2Bridge experimental Bluetooth driver bridge')
    parser.add_argument('--monitor',action='store_true',help='test Bluetooth and motion without creating a virtual controller')
    parser.add_argument('--calibrate',action='store_true',help='keep controller still to save gyro bias')
    parser.add_argument('--test-rumble',action='store_true',help='brief left/right actuator test after connection')
    parser.add_argument('--duration',type=float,default=0,help='exit after this many seconds (0: keep running)')
    parser.add_argument('--stop',action='store_true',help='stop the running bridge cleanly')
    parser.add_argument('--verbose-usb',action='store_true',help='log USB initialization for diagnostics')
    parser.add_argument('--settings',action='store_true',help='open GL/GR back-button mapping window')
    parser.add_argument('--version',action='version',version=__version__)
    options = parser.parse_args()
    if options.settings:
        from settings_ui import open_settings
        open_settings(ROOT)
        sys.exit(0)
    if options.stop:
        try:
            with socket.create_connection(('127.0.0.1',26759),timeout=2) as control:
                control.sendall(b'stop\n')
                if control.recv(16)!=b'OK\n': raise RuntimeError('unrecognized control listener')
            print('Bridge stopping.')
            sys.exit(0)
        except (OSError,RuntimeError) as error:
            print(f'No running bridge: {error}')
            sys.exit(1)
    handler = RotatingFileHandler(ROOT/'bridge.log',maxBytes=2_000_000,backupCount=2,encoding='utf-8')
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',handlers=[handler,logging.StreamHandler()])
    logging.getLogger('vendor.usbip_server').setLevel(logging.INFO if options.verbose_usb else logging.WARNING)
    try: asyncio.run(main(options))
    except KeyboardInterrupt: pass
    except Exception:
        LOG.exception('Bridge stopped with an error')
        sys.exit(1)
