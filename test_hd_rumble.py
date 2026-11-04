import math
import struct
import unittest
from hd_rumble import HDRumble, FRAME, encode_band_frame, packet_frames
from protocol import SILENT

class HDTests(unittest.TestCase):
    def setUp(self):
        self.now=10.;self.sent=[]
        self.hd=HDRumble(lambda:True,clock=lambda:self.now)
        class Transport:
            def sendto(_,data,addr): self.sent.append((data,addr))
        self.hd.connection_made(Transport());self.addr=('127.0.0.1',1234)

    def frame(self,seq=1,values=(1,160,.5,320,0,160,0,320),**kw):
        fields=dict(magic=b'PC2H',version=1,flags=0,ttl=200,reserved=0)
        fields.update(kw)
        return FRAME.pack(fields['magic'],fields['version'],fields['flags'],seq,fields['ttl'],fields['reserved'],123,*values)

    def test_independent_side_and_bands(self):
        self.hd.datagram_received(self.frame(),self.addr);self.now+=.02
        left,right=self.hd.frames()[-1]
        n=int.from_bytes(left,'little');r=int.from_bytes(right,'little')
        self.assertEqual(n&511,274);self.assertEqual((n>>20)&511,391)
        self.assertEqual((n>>10)&1023,450);self.assertEqual((n>>30)&1023,225)
        self.assertEqual((r>>10)&1023,0);self.assertEqual((r>>30)&1023,0)
        self.assertEqual(len(packet_frames(17,((left,right),)*3)),33)

    def test_temporal_subframes_and_watchdog(self):
        self.hd.datagram_received(self.frame(),self.addr)
        self.now+=.006;self.hd.datagram_received(self.frame(2,values=(.2,80,.1,640,0,160,0,320)),self.addr)
        self.now=10.016;frames=self.hd.frames()
        self.assertNotEqual(frames[0],frames[1]);self.assertEqual(frames[1],frames[2])
        self.now+=.21;self.assertFalse(self.hd.active());self.assertEqual(self.hd.frames(),((SILENT,SILENT),)*3)

    def test_invalid_replay_peer_and_sequence_wrap(self):
        self.hd.datagram_received(self.frame(0xffffffff),self.addr)
        self.hd.datagram_received(self.frame(0),self.addr)
        self.assertEqual(self.hd.accepted,2)
        bad=[self.frame(0),self.frame(1,ttl=201),self.frame(1,flags=1),self.frame(1,values=(math.nan,160,0,320,0,160,0,320)),self.frame(1)[:-1]]
        for packet in bad:self.hd.datagram_received(packet,self.addr)
        self.hd.datagram_received(self.frame(1),('127.0.0.1',1235))
        self.assertEqual(self.hd.invalid,6);self.assertEqual(self.hd.accepted,2)

    def test_capability(self):
        self.hd.datagram_received(struct.pack('<4sI',b'PC2Q',1),self.addr)
        self.assertEqual(struct.unpack('<4sIII',self.sent[0][0]),(b'PC2A',1,3,200))

if __name__=='__main__':unittest.main()
