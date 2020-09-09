"""
Defines class and functions to handle GUIDs.
"""
import struct


from .utils import str2bytes


class GUID:
    """GUID class"""
    def __init__(self, raw_data, *, mixed_endian=False):
        if isinstance(raw_data, str):
            raw_data = raw_data.replace("{", "")
            raw_data = raw_data.replace("}", "")
            raw_data = raw_data.replace("-", "")
            raw_data = str2bytes(raw_data)
        self._raw_data = raw_data
        if mixed_endian:
            gp1, gp2, gp3 = struct.unpack("<LHH", raw_data[0: 8])
        else:
            gp1, gp2, gp3 = struct.unpack(">LHH", raw_data[0: 8])
        gp4, gp5, gp6 = struct.unpack(">HHL", raw_data[8:16])
        gp5 = (gp5 << 32 ) | gp6
        self.gp1, self.gp2, self.gp3 = gp1, gp2, gp3
        self.gp4, self.gp5           = gp4, gp5
        self._repr_str  = f"{gp1:08x}-{gp2:04x}-{gp3:04x}-{gp4:04x}-{gp5:012x}".upper()

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
