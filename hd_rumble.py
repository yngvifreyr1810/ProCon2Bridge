"""GPL-3.0-or-later. Loopback transport retaining per-side, per-band effects.

Frequency codes are an experimental logarithmic profile, not measured HD Rumble 2
calibration. See HD-RUMBLE.md. No Nintendo waveform or firmware is included.
"""
import asyncio
from collections import deque
import math
import struct
import time
from protocol import SILENT

FRAME = struct.Struct('<4sHHIHHQ8f')

def encode_band_frame(values, strength=1.):
    la,lf,ha,hf = values
    def frequency(hz):
        return max(1,min(511,round(274+117*math.log2(hz/160))))
    def amplitude(a):
        return max(0,min(800,round(a*450*strength)))
    # BLE is LF-first (USB is HF-first). Leave the unverified tone flags clear;
    # clamp to the donor's 9-bit BLE carrier range rather than guessing bit 9.
    bits = frequency(lf) | amplitude(la)<<10 | frequency(hf)<<20 | amplitude(ha)<<30
    return bits.to_bytes(5,'little')

def packet_frames(sequence, pairs):
    if len(pairs)!=3 or any(len(f)!=5 for p in pairs for f in p) or any(len(p)!=2 for p in pairs):
        raise ValueError('expected three left/right haptic frame pairs')
    header=bytes([0x50 | (sequence&15)])
    return b'\0'+header+b''.join(p[0] for p in pairs)+header+b''.join(p[1] for p in pairs)

class HDRumble(asyncio.DatagramProtocol):
    def __init__(self, connected=lambda:False, strength=1., clock=time.monotonic):
        self.connected,self.strength,self.clock=connected,strength,clock
        self.events=deque(maxlen=256)
        self.owner=None;self.sequence=None;self.until=0
        self.last=(SILENT,SILENT)
        self.accepted=self.invalid=0

    def connection_made(self, transport): self.transport=transport

    def reset(self):
        self.events.clear();self.owner=None;self.sequence=None;self.until=0
        self.last=(SILENT,SILENT)

    def datagram_received(self, data, addr):
        if addr[0]!='127.0.0.1': return
        if data==struct.pack('<4sI',b'PC2Q',1):
            self.transport.sendto(struct.pack('<4sIII',b'PC2A',1,3 if self.connected() else 2,200),addr)
            return
        try:
            if len(data)!=FRAME.size: raise ValueError()
            magic,version,flags,seq,ttl,reserved,stamp,*v=FRAME.unpack(data)
            if magic!=b'PC2H' or version!=1 or flags or reserved or not 1<=ttl<=200: raise ValueError()
            if any(not math.isfinite(x) for x in v): raise ValueError()
            if any(not 0<=v[i]<=2 for i in (0,2,4,6)) or any(not 1<=v[i]<=1250 for i in (1,3,5,7)): raise ValueError()
            now=self.clock()
            if now<self.until and self.owner!=addr: raise ValueError()
            if now<self.until and self.sequence is not None and not 0<(seq-self.sequence)&0xffffffff<0x80000000: raise ValueError()
            if now>=self.until:
                self.events.clear();self.last=(SILENT,SILENT)
            self.owner,self.sequence,self.until=addr,seq,now+ttl/1000
            pair=(encode_band_frame(v[:4],self.strength),encode_band_frame(v[4:],self.strength))
            self.events.append((now,pair));self.accepted+=1
        except (ValueError,struct.error,OverflowError): self.invalid+=1

    def active(self): return self.clock()<self.until

    def frames(self, now=None):
        now=self.clock() if now is None else now
        if now>=self.until:
            self.events.clear();self.last=(SILENT,SILENT)
            return (self.last,)*3
        out=[]
        # One packet of lookbehind retains three distinct 5 ms subframes.
        for t in (now-.015,now-.010,now-.005):
            while self.events and self.events[0][0]<=t: self.last=self.events.popleft()[1]
            out.append(self.last)
        return tuple(out)
