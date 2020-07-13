"""
This module handles reading from and writing to a FAT32 filesystem.
"""
import datetime
import struct
import sys


from collections import namedtuple


attributes = {
    "read-only": 0x01, 
    "hidden"   : 0x02,
    "system"   : 0x04,
    "volume-id": 0x08,
    "directory": 0x10,
    "archive"  : 0x20,
}


class FileRecord:
    def __init__(self, data):
        self._raw_data   = data
        self._name       = b""
        self._ext        = b""
        self._size       = -1
        self._attributes = {k: False for k in attributes}
        self._cluster    = -1
        self._ts_create  = None
        self._ts_last    = None
        self._ts_mod     = None
        # that's all for real attributes of a file record
        self.verbose     = False
    
    def __repr__(self):
        if self.verbose:
            return (
                f"< DirectoryEntry: {self.name}.{self.ext}\n"
                f"  {'cluster':12}:{self.cluster:>12}\n" 
                f"  {'size':12}:{self.size:>12}\n" 
                f"  {'created':12}:{self.created:>12}\n" 
                f"  {'modified':12}:{self.modified:>12}\n" 
                f"  {'accessed':12}:{self.accessed:>12}\n" 
                f"  {'attributes':12}:{self._attrs2str():>12}\n" 
                f">"
            )
        return f"< DirectoryEntry: {self.name}.{self.ext}>"
    
    def _attrs2str(self):
        ret = [
            k[0].upper() if v else k[0]
            for (k, v) in self._attributes.items()
        ]
        return "".join(ret)


class Filesystem:
    pass
