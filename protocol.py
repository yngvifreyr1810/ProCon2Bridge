"""Pro Controller 2 BLE protocol adapter. SPDX-License-Identifier: GPL-3.0-or-later.

Protocol layouts: Switch2Connect (TommyWabg) and pad2go (Patrick DeAngelis).
See THIRD_PARTY.md. This is an experimental user-mode bridge, not a signed driver.
"""
import math
import struct
from dataclasses import dataclass

WRITE = '649d4ac9-8eb7-4e6c-af44-1ea54fe5f005'
RESPONSE = 'c765a961-d9d8-4d36-a20a-5315b111836a'
INPUT = 'ab7de9be-89fe-49ad-828f-118f09df7fd2'
RUMBLE = 'cc483f51-9258-427d-a939-630c31f72b05'
BUTTONS = dict(Y=1, X=2, B=4, A=8, R=0x40, ZR=0x80, MINUS=0x100,
    PLUS=0x200, R_STICK=0x400, L_STICK=0x800, HOME=0x1000, CAPTURE=0x2000,
    C=0x4000, DOWN=0x10000, UP=0x20000, RIGHT=0x40000, LEFT=0x80000,
    L=0x400000, ZL=0x800000, GR=0x1000000, GL=0x2000000)
INIT = [(3,13,'0100ffffffffffff'),(7,1,''),(22,1,''),(21,3,'00'),
    (12,2,'94000000'),(17,3,''),(10,8,'01ffffffffffffffff3500460000000000000000'),
    (12,4,'94000000'),(3,10,'09000000'),(16,1,''),(1,12,''),(9,7,'0100000000000000')]

def is_pro2(device, adv):
    data = adv.manufacturer_data.get(0x0553, b'')
    return len(data) >= 16 and data[3:7] == bytes.fromhex('7e056920')

def command(cmd, sub, data=b''):
    if len(data) > 255:
        raise ValueError('command payload too large')
    return bytes([cmd,0x91,1,sub,0,len(data),0,0]) + data

def stick(data):
    v = int.from_bytes(data[:3], 'little')
    return v & 4095, (v >> 12) & 4095

@dataclass
class Calibration:
    center: tuple = (2048,2048)
    negative: tuple = (1500,1500)
    positive: tuple = (1500,1500)

    @classmethod
    def parse(cls, data):
        if len(data) < 9:
            return cls()
        center, negative, positive = [stick(data[i:i+3]) for i in (0,3,6)]
        if any(not 1024 <= c <= 3072 for c in center) or any(
            not 1 <= n <= c or not 1 <= p <= 4095-c
            for c,n,p in zip(center,negative,positive)):
            return cls()
        return cls(center,negative,positive)

    def apply(self, values, deadzone=.03):
        out = tuple(max(-1., min(1., (v-c)/(p if v >= c else n)))
            for v,c,n,p in zip(values,self.center,self.negative,self.positive))
        return (0.,0.) if math.hypot(*out) < deadzone else out

@dataclass
class Sample:
    buttons: int = 0
    left: tuple = (0.,0.)
    right: tuple = (0.,0.)
    accel: tuple = (0,0,0)
    gyro: tuple = (0,0,0)
    voltage: float = 0.
    timestamp: int = 0

    @classmethod
    def parse(cls, data, calibrations, deadzone=.03):
        if len(data) < 60:
            raise ValueError('short Pro Controller 2 report')
        return cls(int.from_bytes(data[4:8],'little') & 0x3ffffff,
            calibrations[0].apply(stick(data[10:13]),deadzone),
            calibrations[1].apply(stick(data[13:16]),deadzone),
            struct.unpack_from('<3h',data,48),struct.unpack_from('<3h',data,54),
            int.from_bytes(data[31:33],'little')/1000,
            int.from_bytes(data[:4],'little'))

def remap_buttons(buttons, mappings):
    original = buttons
    for source in mappings:
        buttons &= ~BUTTONS[source]
    for source,target in mappings.items():
        mask = BUTTONS[source]
        if original & mask and target != 'NONE':
            buttons |= BUTTONS[target]
    return buttons

def pack_stick(x,y):
    # SDL scales the advertised +/-2047 factory span by 0.7.
    x,y = (max(0,min(4095,round(2048+v*1433))) for v in (x,y))
    return (x | y << 12).to_bytes(3,'little')

def pro2_to_switch_vector(values):
    """Rotate Pro 2 sensor coordinates into Switch 1 Pro wire coordinates.

    SDL's Switch 1 driver maps wire (x,y,z) to (-y,z,-x), whereas native
    Switch 2 sensors map to (x,z,-y). Emit (y,-x,z) so those paths agree.
    This is the same proper rotation for gyro AND acceleration, not an
    aim-axis inversion. Bias remains in the original physical sensor frame.
    """
    x,y,z = values
    return y,-x,z

def switch_report(sample, gyro_bias=(0,0,0), gyro_scale=1.):
    out = bytearray(50)
    out[0],out[2],out[12] = 0x30,0x8e,8
    # Only controls available in a Switch 1 Pro input report are exposed here.
    buttons = sample.buttons & 0xff3fff
    out[3:6] = buttons.to_bytes(3,'little')
    out[6:9],out[9:12] = pack_stick(*sample.left),pack_stick(*sample.right)
    ax,ay,az = pro2_to_switch_vector(sample.accel)
    gx,gy,gz = pro2_to_switch_vector(tuple((g-b)*gyro_scale for g,b in zip(sample.gyro,gyro_bias)))
    imu = struct.pack('<6h',*(max(-32768,min(32767,round(v))) for v in
        (ax,ay,az,gx,gy,gz)))
    for offset in (13,25,37):
        out[offset:offset+12] = imu
    return bytes(out)

def vibration_frame(lf=0,hf=0,lf_freq=0xe1,hf_freq=0x1e1):
    lf,hf = (max(0,min(1023,round(v))) for v in (lf,hf))
    value = (lf_freq & 511) | lf << 10 | (hf_freq & 511) << 20 | hf << 30
    return value.to_bytes(5,'little')

SILENT = vibration_frame()

def decode_switch_rumble(data, strength=1.):
    """Frequency/amplitude conversion from Switch2Connect, not a bit-exact pass-through."""
    if len(data) != 4:
        raise ValueError('rumble frame must be 4 bytes')
    def linear(encoded):
        if encoded <= 0: return 0.
        if encoded >= 32: return 2**(encoded/32)/8.7
        if encoded >= 16: return 2**(encoded/16)/17.
        return encoded/16*.12
    hf = data[1] >> 1
    lf = max(0,(data[3]-64)*2 + ((data[2] >> 7)&1))
    # Switch 1 carrier codes are not Switch 2 carrier codes. Use the Pro
    # translation from Switch2Connect's set_vibration(Switch1) path:
    # expand its compressed HF range; keep ordinary LF in the Pro 2 bass band.
    hf_freq = data[0] | ((data[1]&1)<<8)
    pro_lf_freq = 0xe1
    pro_hf_freq = max(1,min(511,int(hf_freq*4.167)))
    return vibration_frame(linear(lf)*800*strength,linear(hf)*800*strength,
        pro_lf_freq,pro_hf_freq)

def rumble_packet(sequence,left=SILENT,right=SILENT):
    if len(left) != 5 or len(right) != 5:
        raise ValueError('Pro 2 haptic frames must be 5 bytes')
    header = bytes([0x50 | (sequence & 15)])
    return b'\0' + header + left*3 + header + right*3
