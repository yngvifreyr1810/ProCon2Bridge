"""HID-only USB/IP Switch Pro device. GPL-3.0-or-later.

Adapts the unmodified Switch2Connect server, omitting its unused WinUSB bulk
interface so Windows needs only its built-in HID driver for the virtual device.
"""
import struct
import time
import queue
from vendor.usbip_server import (USBIPProControllerServer,
    SWITCH1_PRO_REPORT_DESCRIPTOR, USBIP_VERSION, OP_REP_DEVLIST, USBIP_RET_SUBMIT)

class NativeProServer(USBIPProControllerServer):
    def _handle_spi_read(self,data):
        if len(data)>=16:
            address=int.from_bytes(data[11:15],'little')
            length=data[15]
            if 0x6020<=address and address+length<=0x6038:
                # Data is already bias-corrected by the bridge. Advertising
                # physical offsets copied from another controller would make
                # SDL subtract an unrelated bias and create continuous drift.
                calibration=struct.pack('<12h',0,0,0,16384,16384,16384,
                    0,0,0,13371,13371,13371)
                reply=list(data[11:15])+[length]+list(calibration[address-0x6020:address-0x6020+length])
                return self._build_subcommand_reply(0x10,ack=0x90,reply_data=reply)
        return super()._handle_spi_read(data)

    def _get_device_desc(self):
        desc=bytearray(super()._get_device_desc())
        desc[-1]=1
        return bytes(desc)

    def _send_devlist(self,sock):
        sock.sendall(struct.pack('!HHII',USBIP_VERSION,OP_REP_DEVLIST,0,1)
            +self._get_device_desc()+bytes([3,0,0,0]))

    def _handle_control_request(self,setup,transfer_length,out_data=b''):
        req_type,request,value,index,length=struct.unpack('<BBHHH',setup)
        if request==6 and req_type in (0x80,0x81):
            kind,idx=value>>8,value&255
            if kind==0x22:
                return SWITCH1_PRO_REPORT_DESCRIPTOR[:length]
            if kind==2:
                desc=bytearray(super()._handle_control_request(
                    struct.pack('<BBHHH',req_type,request,value,index,255),255))
                # Config + interface 0 + HID descriptor + two interrupt endpoints.
                desc=desc[:41]
                struct.pack_into('<H',desc,2,len(desc))
                desc[4]=1
                struct.pack_into('<H',desc,25,len(SWITCH1_PRO_REPORT_DESCRIPTOR))
                return bytes(desc[:length])
            if kind==3 and idx==3:
                text='PC2BRIDGE01'.encode('utf-16le')
                return (bytes([len(text)+2,3])+text)[:length]
            if kind==3 and idx==0xee:
                return b'' # No WinUSB interface to associate with MS OS descriptors.
        if req_type==0 and request in (9,11):
            return b'' # SET_CONFIGURATION / SET_INTERFACE success.
        return super()._handle_control_request(setup,transfer_length,out_data)

    def _stamp_timer_byte(self,report):
        report[1]=(time.monotonic_ns()//5_000_000)&255

    def update_state(self,state_bytes):
        super().update_state(state_bytes)
        # Queue contains the fresh IMU report. Do not repeat angular velocity
        # when the USB host polls again before the next BLE notification.
        with self.lock:
            for offset in (19,31,43):
                self.last_state[offset:offset+6]=b'\0'*6

    def _process_deferred_in_urb(self,sock,seqnum,devid,direction,ep):
        if ep!=1:
            return super()._process_deferred_in_urb(sock,seqnum,devid,direction,ep)
        # SDL waits 100 ms for initialization acknowledgements. The upstream
        # 100 ms input-queue wait can hold an ACK past that deadline when there
        # is no physical controller input yet. Check the priority queue at 2 ms.
        end=time.monotonic()+.015
        while True:
            try:
                data=self.subcmd_reply_queue.get_nowait()
                break
            except queue.Empty:
                try:
                    data=self.input_queue.get_nowait()
                    break
                except queue.Empty:
                    if time.monotonic()>=end or not self.running:
                        with self.lock:data=bytes(self.last_state)
                        break
                    time.sleep(.002)
        data=bytearray(data)
        if data and data[0]==0x30:self._stamp_timer_byte(data)
        # Windows HID reads must match the 64-byte USB report descriptor.
        # The upstream Joy-Con transport uses 50-byte Bluetooth-shaped reports.
        data=data.ljust(64,b'\0')[:64]
        header=struct.pack('!IIIIIiIIII8s',USBIP_RET_SUBMIT,seqnum,devid,
            direction,ep,0,len(data),0,0,0,b'\0'*8)
        with self.send_lock:sock.sendall(header+data)
