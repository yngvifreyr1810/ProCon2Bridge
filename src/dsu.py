"""Local-only CemuHook motion server v1001. GPL-3.0-or-later."""
import asyncio
import secrets
import struct
import time
import zlib
from protocol import BUTTONS

def packet(kind, payload=b'', server=1, magic=b'DSUS'):
    body = struct.pack('<I',kind)+payload
    out = bytearray(struct.pack('<4sHHII',magic,1001,len(body),0,server)+body)
    struct.pack_into('<I',out,8,zlib.crc32(out))
    return bytes(out)

class DSU(asyncio.DatagramProtocol):
    def __init__(self):
        self.transport = None
        self.clients = {}
        self.server = secrets.randbits(32)
        self.mac = bytes.fromhex('025043320001')
        self.connected = False
        self.counter = 0

    def connection_made(self, transport): self.transport = transport

    def info(self, pad=0):
        active = self.connected and pad == 0
        return bytes([pad,2 if active else 0,2 if active else 0,2 if active else 0]) + self.mac + bytes([0,0])

    def datagram_received(self, data, address):
        if len(data) < 20 or data[:4] != b'DSUC': return
        version,size,crc = struct.unpack_from('<HHI',data,4)
        if version > 1001 or len(data) != size+16: return
        check = bytearray(data); check[8:12] = b'\0'*4
        if zlib.crc32(check) != crc: return
        kind, = struct.unpack_from('<I',data,16)
        if kind == 0x100000:
            self.transport.sendto(packet(kind,struct.pack('<H',1001),self.server),address)
        elif kind == 0x100001 and len(data) >= 24:
            count, = struct.unpack_from('<i',data,20)
            if not 0 <= count <= 4 or len(data) != 24+count: return
            for pad in data[24:]:
                if pad < 4: self.transport.sendto(packet(kind,self.info(pad),self.server),address)
        elif kind == 0x100002 and len(data) == 28:
            flags,pad = data[20:22]
            if flags == 0 or flags&1 and pad == 0 or flags&2 and data[22:28] == self.mac:
                self.clients[address] = time.monotonic()

    def publish(self,sample,bias,gyro_scale):
        if not self.transport: return
        now = time.monotonic()
        targets = [a for a,t in self.clients.items() if now-t < 5]
        self.clients = {a:t for a,t in self.clients.items() if now-t < 5}
        if not targets: return
        b = sample.buttons
        def bit(name,value=1): return value if b & BUTTONS[name] else 0
        b1 = bit('LEFT',128)|bit('DOWN',64)|bit('RIGHT',32)|bit('UP',16)|bit('PLUS',8)|bit('R_STICK',4)|bit('L_STICK',2)|bit('MINUS')
        b2 = bit('Y',128)|bit('B',64)|bit('A',32)|bit('X',16)|bit('R',8)|bit('L',4)|bit('ZR',2)|bit('ZL')
        self.counter = (self.counter+1)&0xffffffff
        payload = bytearray(self.info()); payload[-1] = 1
        payload += struct.pack('<I',self.counter)
        payload += bytes([b1,b2,bit('HOME'),bit('CAPTURE')])
        payload += bytes(round(127.5+127.5*v) for v in (*sample.left,*sample.right))
        payload += bytes(bit(n,255) for n in ('LEFT','DOWN','RIGHT','UP','Y','B','A','X','R','L','ZR','ZL'))
        payload += b'\0'*12
        ax,ay,az = sample.accel
        gx,gy,gz = ((g-v)*gyro_scale/14.285714 for g,v in zip(sample.gyro,bias))
        payload += struct.pack('<Q6f',time.monotonic_ns()//1000,-ax/4096,-az/4096,ay/4096,gx,-gz,gy)
        out = packet(0x100002,payload,self.server)
        for address in targets: self.transport.sendto(out,address)
