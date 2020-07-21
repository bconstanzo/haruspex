"""
This module handles reading from and writing to a FAT32 filesystem.
"""
import datetime
import struct
import sys


from collections import namedtuple

# TODO: read https://stackoverflow.com/questions/13775893/converting-struct-to-byte-and-back-to-struct
#       and research a bit into this being a reasonable way to convert bytes
#       into structs (and back).


ATTRIBUTES = {
    "read-only": 0x01, 
    "hidden"   : 0x02,
    "system"   : 0x04,
    "volume-id": 0x08,
    "directory": 0x10,
    "archive"  : 0x20,
}

FILENAME_CHARS = set(b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_-")


def _fat32_time(bytes_, mili=b"\x00"):
    """
    Receives date + time bytes in `bytes`, and returns a datetime object.
    Checks for pathological 0xffff patterns
    """
    raw_date, raw_time, = struct.unpack(">HH", bytes_)
    seconds += mili[0] / 200


class FileRecord:
    def __init__(self, data):
        self._raw_data   = data
        self._name       = b""
        self._ext        = b""
        self._size       = -1
        self._attributes = {k: False for k in ATTRIBUTES}
        self._cluster    = -1
        self._ts_create  = None
        self._ts_last    = None
        self._ts_mod     = None
        # that's all for real attributes of a file record
        self.verbose     = False
        self._parse()
    
    # The Properties
    # (these could be done with metaclasses, but...)
    @property
    def raw_data(self):
        return self._raw_data
    
    @raw_data.setter
    def raw_data(self, value):
        pass  # let's make it read-only for the moment

    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        if isinstance(value, str):
            value = bytes(value, "utf-8")
        name = b"".join([c for c in value.upper() if c in FILENAME_CHARS])
        name = name[:8],   # byebye long names!
        # let's check if there's an ext, for the lazy user
        if b"." in value:
            name, dot, ext = value.rpartition(b".")
            self._ext = ext[-3:]
        self._name = value # 
        # will not enforce name uniqueness, just being uppercase and within
        # valid range of characters
    
    @property
    def ext(self):
        return self._ext
    
    @ext.setter
    def ext(self, value):
        if isinstance(value, str):
            value = bytes(value, "utf-8")
        ext = b"".join([c for c in value.upper() if c in FILENAME_CHARS])
        ext = ext[:3]
        self._ext = ext
    
    @property
    def size(self):
        return self._size
    
    @size.setter
    def size(self, value):
        if value > 0xffffffff:
            value = 0xffffffff
        self._size = value
    
    @property
    def attributes(self):
        return self._attributes
    
    @attributes.setter
    def attributes(self, value):
        # let's cleanup in case the given dict has some extra keys
        value = {k:v for k, v in value.items() if k in ATTRIBUTES}
        self._attributes.update(value)
    
    def __repr__(self):
        if self.verbose:
            return (
                f"< DirectoryEntry: {self.name}.{self.ext}\n"
                f"  {'size':12}:{self.size:>12}\n" 
                f"  {'attributes':12}:{self._attrs2str():>12}\n" 
                f"  {'cluster':12}:{self.cluster:>12}\n" 
                f"  {'created':12}:{self.created:>12}\n" 
                f"  {'modified':12}:{self.modified:>12}\n" 
                f"  {'accessed':12}:{self.accessed:>12}\n" 
                f">"
            )
        return f"< DirectoryEntry: {self.name}.{self.ext}>"
    
    def _attrs2str(self):
        ret = [
            k[0].upper() if v else k[0]
            for (k, v) in self._attributes.items()
        ]
        return "".join(ret)
    
    def _parse(self):
        """
        Parses self._raw_data and updates the properties
        """
        pass


class Filesystem:
    pass
