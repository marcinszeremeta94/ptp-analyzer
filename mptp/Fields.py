import struct
from scapy.fields import XStrFixedLenField, BitField


class TimestampField(BitField):
    def __init__(self, name, default):
        BitField.__init__(self, name, default, 80)

    def any2i(self, pkt, val):
        if val is None:
            return val
        ival = int(val)
        fract = int((val - ival) * 1e9)
        return (ival << 32) | fract

    def i2h(self, pkt, val):
        int_part = val >> 32
        frac_part = val & (1 << 32) - 1
        res = dict()
        res['s'] = int_part
        res['ns'] = frac_part
        return res


class PortIdentityField(XStrFixedLenField):
    encoding = "!BBBBBBBBh"

    def __init__(self, name, default):
        XStrFixedLenField.__init__(self, name, default, length=10)

    def i2h(self, pkt, val):
        if val is None:
            return "None"
        p = struct.unpack(self.encoding, val)
        return f"{p[0]:02x}:{p[1]:02x}:{p[2]:02x}:{p[5]:02x}:{p[6]:02x}:{p[7]:02x}/{p[8]}"

    def i2repr(self, pkt, x):
        return self.i2h(pkt, x)
