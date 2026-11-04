import asyncio
import dataclasses
import struct
import unittest
import zlib
import time
import threading
from unittest.mock import patch
from protocol import *
from dsu import DSU,packet
from native_pro import NativeProServer
from vendor.usbip_server import SWITCH1_PRO_REPORT_DESCRIPTOR

class Transport:
    def __init__(self): self.sent=[]
    def sendto(self,data,address): self.sent.append((data,address))

class ProtocolTests(unittest.TestCase):
    def test_decode_signed_real_layout(self):
        raw=bytearray(60)
        struct.pack_into('<II',raw,0,123,BUTTONS['A']|BUTTONS['GL']|0xfc000000)
        raw[10:13]=(2048|2048<<12).to_bytes(3,'little')
        raw[13:16]=raw[10:13]
        struct.pack_into('<H',raw,31,3300)
        struct.pack_into('<6h',raw,48,-4096,256,1,-500,1000,-32768)
        s=Sample.parse(raw,[Calibration(),Calibration()])
        self.assertEqual(s.buttons,BUTTONS['A']|BUTTONS['GL'])
        self.assertEqual(s.accel,(-4096,256,1))
        self.assertEqual(s.gyro,(-500,1000,-32768))
        self.assertEqual(s.left,(0,0));self.assertEqual(s.voltage,3.3)
        with self.assertRaises(ValueError):Sample.parse(raw[:59],[Calibration()]*2)

    def test_factory_stick_calibration(self):
        cal=Calibration.parse(b''.join((x|y<<12).to_bytes(3,'little') for x,y in ((1972,2093),(1641,1622),(1649,1577))))
        self.assertEqual(cal.apply((1972,2093)),(0,0))
        self.assertEqual(cal.apply((3621,471)),(1,-1))
        self.assertEqual(Calibration.parse(b'\xff'*11),Calibration())

    def test_virtual_switch_imu_and_buttons(self):
        report=switch_report(Sample(buttons=BUTTONS['A']|BUTTONS['GL']|BUTTONS['C'],
            left=(1,-1),accel=(1,-2,4096),gyro=(100,200,-300)),(10,20,30))
        self.assertEqual(len(report),50);self.assertEqual(report[0],0x30)
        self.assertEqual(int.from_bytes(report[3:6],'little'),BUTTONS['A'])
        self.assertEqual(stick(report[6:9]),(3481,615))
        for offset in (13,25,37):
            self.assertEqual(struct.unpack_from('<6h',report,offset),(-2,-1,4096,180,-90,-330))

    def test_switch_wire_then_sdl_matches_native_pro2_sensor_basis(self):
        # Expected SDL physical Switch 2 basis is (x,z,-y), independently of
        # our Switch 1 encoder. Exercise every physical axis and both signs.
        for axis in range(3):
            for sign in (-1,1):
                raw=[0,0,0];raw[axis]=sign*1000
                report=switch_report(Sample(accel=tuple(raw),gyro=tuple(raw)))
                for offset in (13,25,37):
                    ax,ay,az,gx,gy,gz=struct.unpack_from('<6h',report,offset)
                    expected=(raw[0],raw[2],-raw[1])
                    self.assertEqual((-ay,az,-ax),expected)
                    self.assertEqual((-gy,gz,-gx),expected)

    def test_stationary_gravity_and_pitch_stay_in_the_correct_sdl_axes(self):
        # Level controller: +Z raw accel becomes SDL +Y gravity. Pitch is
        # physical X; it must become SDL pitch X, not roll or yaw.
        report=switch_report(Sample(accel=(0,0,4096),gyro=(1000,0,0)))
        ax,ay,az,gx,gy,gz=struct.unpack_from('<6h',report,13)
        self.assertEqual((-ay,az,-ax),(0,4096,0))
        self.assertEqual((-gy,gz,-gx),(1000,0,0))

    def test_remap_swaps_and_extra_buttons(self):
        self.assertEqual(remap_buttons(BUTTONS['A'],{'A':'B','B':'A'}),BUTTONS['B'])
        self.assertEqual(remap_buttons(BUTTONS['GL']|BUTTONS['A'],{'GL':'B','C':'NONE'}),BUTTONS['A']|BUTTONS['B'])

    def test_rumble_independent_sides_and_limits(self):
        left=vibration_frame(lf=5000,hf=-4,lf_freq=17,hf_freq=300)
        value=int.from_bytes(left,'little')
        self.assertEqual(value&511,17);self.assertEqual((value>>10)&1023,1023)
        self.assertEqual((value>>20)&511,300);self.assertEqual(value>>30,0)
        result=rumble_packet(17,left,SILENT)
        self.assertEqual(len(result),33);self.assertEqual(result[:2],b'\0Q')
        self.assertEqual(result[2:17],left*3);self.assertEqual(result[18:],SILENT*3)
        zero=decode_switch_rumble(bytes.fromhex('00014040'))
        value=int.from_bytes(zero,'little')
        self.assertEqual((value>>10)&1023,0);self.assertEqual(value>>30,0)

    def test_sdl_rumble_uses_pro2_carriers_not_switch1_carrier_codes(self):
        # Captured SDL_RumbleGamepad output carrier bytes. Reusing 61/116
        # directly as Pro 2 codes produces almost imperceptible output.
        value=int.from_bytes(decode_switch_rumble(bytes.fromhex('745c3d60')),'little')
        self.assertEqual(value&511,225)
        self.assertEqual((value>>20)&511,483)
        self.assertGreater((value>>10)&1023,0)
        self.assertGreater(value>>30,0)

    def test_zero_rumble_remains_silent_after_carrier_translation(self):
        value=int.from_bytes(decode_switch_rumble(bytes.fromhex('00014040')),'little')
        self.assertEqual((value>>10)&1023,0)
        self.assertEqual((value>>30)&1023,0)

class DSUTests(unittest.TestCase):
    def setUp(self):
        self.server=DSU();self.transport=Transport()
        self.server.connection_made(self.transport)
        self.addr=('127.0.0.1',1234)

    def test_version_and_crc(self):
        self.server.datagram_received(packet(0x100000,magic=b'DSUC'),self.addr)
        response=self.transport.sent[0][0]
        self.assertEqual(response[:4],b'DSUS')
        check=bytearray(response);expected=struct.unpack_from('<I',check,8)[0];check[8:12]=b'\0'*4
        self.assertEqual(zlib.crc32(check),expected)
        self.assertEqual(struct.unpack_from('<H',response,20)[0],1001)

    def test_motion_payload_and_subscription_validation(self):
        subscribe=packet(0x100002,b'\0'*8,magic=b'DSUC')
        damaged=bytearray(subscribe);damaged[-1]=1
        self.server.datagram_received(bytes(damaged),self.addr)
        self.assertFalse(self.server.clients)
        self.server.datagram_received(subscribe,self.addr)
        self.server.connected=True
        self.server.publish(Sample(accel=(4096,0,0),gyro=(1428,0,0)),(0,0,0),1)
        out=self.transport.sent[-1][0]
        self.assertEqual(len(out),100)
        self.assertEqual(out[21],2)
        self.assertEqual(struct.unpack_from('<3f',out,76),(-1.,0.,0.))
        self.assertAlmostEqual(struct.unpack_from('<f',out,88)[0],99.96,places=2)

class NativeProTests(unittest.TestCase):
    def test_virtual_sensor_calibration_has_no_foreign_gyro_bias(self):
        server=NativeProServer(bus_id='8-32')
        request=bytearray(16);request[11:15]=(0x6020).to_bytes(4,'little');request[15]=24
        reply=server._handle_spi_read(request)
        self.assertEqual(struct.unpack_from('<3h',reply,32),(0,0,0))
        self.assertEqual(struct.unpack_from('<3h',reply,38),(13371,13371,13371))
        self.assertEqual(struct.unpack_from('<3h',reply,20),(0,0,0))

    def test_hid_only_configuration_and_descriptor(self):
        server=NativeProServer(bus_id='8-32')
        setup=struct.pack('<BBHHH',0x80,6,0x200,0,255)
        desc=server._handle_control_request(setup,255)
        self.assertEqual(len(desc),41)
        self.assertEqual(struct.unpack_from('<H',desc,2)[0],41)
        self.assertEqual(desc[4],1)
        self.assertEqual(desc[13],2)
        self.assertEqual(struct.unpack_from('<H',desc,25)[0],len(SWITCH1_PRO_REPORT_DESCRIPTOR))
        hid=server._handle_control_request(struct.pack('<BBHHH',0x81,6,0x2200,0,1000),1000)
        self.assertEqual(hid,SWITCH1_PRO_REPORT_DESCRIPTOR)

    def test_stale_usb_reads_do_not_repeat_motion(self):
        server=NativeProServer(bus_id='8-32')
        report=switch_report(Sample(gyro=(100,200,300)))
        server.update_state(report)
        fresh=server.input_queue.get_nowait()
        self.assertEqual(struct.unpack_from('<3h',fresh,19),(200,-100,300))
        self.assertEqual(struct.unpack_from('<3h',server.last_state,19),(0,0,0))

    def test_usb_ack_is_full_length_and_does_not_wait_for_physical_input(self):
        server=NativeProServer(bus_id='8-32');server.running=True
        reply=server._build_subcommand_reply(0x10,ack=0x90,reply_data=[0x3d,0x60,0,0,18]+[0]*18)
        class Socket:
            def sendall(self,data):self.data=data
        sock=Socket()
        # Inject the priority ACK at the first empty-queue wait, without a
        # wall-clock assertion that becomes flaky on a loaded CI machine.
        with patch('native_pro.time.sleep',side_effect=lambda _:server.subcmd_reply_queue.put(reply)) as wait:
            server._process_deferred_in_urb(sock,1,0x10020,1,1)
        wait.assert_called_once_with(.002)
        self.assertEqual(len(sock.data),48+64)
        self.assertEqual(struct.unpack_from('!I',sock.data,24)[0],64)
        self.assertEqual(sock.data[48],0x21)

if __name__=='__main__':unittest.main()
