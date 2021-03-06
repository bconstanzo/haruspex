"""
Defines class and functions to handle GUIDs.
"""
import struct


from .utils import str2bytes


class GUID:
    """GUID class"""
    def __init__(self, data, *, mixed_endian=False):
        if isinstance(data, str):
            data = data.replace("{", "")
            data = data.replace("}", "")
            data = data.replace("-", "")
            data = str2bytes(data)
        self._data = data
        if mixed_endian:
            gp1, gp2, gp3 = struct.unpack("<LHH", data[0: 8])
        else:
            gp1, gp2, gp3 = struct.unpack(">LHH", data[0: 8])
        gp4, gp5, gp6 = struct.unpack(">HHL", data[8:16])
        gp5 = (gp5 << 32 ) | gp6
        self.gp1, self.gp2, self.gp3 = gp1, gp2, gp3
        self.gp4, self.gp5           = gp4, gp5
        self._repr_str  = f"{gp1:08x}-{gp2:04x}-{gp3:04x}-{gp4:04x}-{gp5:012x}".upper()
        self._mixed_endian = mixed_endian

    def __bytes__(self):
        if self._mixed_endian:
            data = struct.pack("<LHH", self.gp1, self.gp2, self.gp3)
        else:
            data = struct.pack(">LHH", self.gp1, self.gp2, self.gp3)
        gp5 = self.gp5 >> 32
        gp6 = self.gp5 & 0x0000ffffffff
        data += struct.pack(">HHL", self.gp4, gp5, gp6)
        return data

    def __repr__(self):
        return f"< GUID: {self._repr_str} >"
    
    def __str__(self):
        return "{" f"{self._repr_str}" "}"
    
    # and to make these dictionary-key-able...
    def __hash__(self):
        return hash(self._repr_str)
    
    def __eq__(self, other):
        if not isinstance(other, GUID):
            return False
        return self._repr_str == other._repr_str
    
    def __ne__(self, other):
        return not(self == other)
