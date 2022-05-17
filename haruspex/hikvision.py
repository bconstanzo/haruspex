"""
Implements data structures and methods to read Hikvision DVR filesystem.

Initially the data structures are based on the paper "Analysis of the HIKVISION
DVR File System" by Han J., Jeong D., Lee S.

As the paper just describes some data structures, but others aren't explained in
detail, there's some research of our own to develop the remaining funcitonality.
"""

import datetime
import struct


class Hikvision:
    def __init__(self, handle, base_address=0):
        """
        Handles reading a Hikvision DVR filesystem.

        :param handle: file-like object pointing to the filesystem
        :param base_address: offset to the filesystem in `handle` (defaults to
            0, usually the filesystem is at the 2nd sector so it'd be an offset
            of 512)
        """
        self._base_address = base_address
        self._handle       = handle
        self._handle.seek(base_address)
        master_sector = self._handle.read(512)
        volsize, _, log_offset, log_size, _, data_offset, _, data_size, \
            data_number, _, tree1_offset, tree1_size, _, tree2_offset,\
            tree2_size = struct.unpack("<Q16sQQ8sQ8sQL4sQL4sQL", master_sector[72:72+108])
        
        self.volume_size  = volsize
        self.log_offset   = log_offset
        self.log_size     = log_size
        self.data_offset  = data_offset
        self.data_size    = data_size
        self.data_number  = data_number
        self.tree1_offset = tree1_offset
        self.tree1_size   = tree1_size
        self.tree2_offset = tree2_offset
        self.tree2_size   = tree2_size
        
    def __repr__(self):
        return f"< Hikvision DVR @ {self._base_address} >"
    
    def __str__(self):
        return (
               "< Hikvision DVR Filesystem:\n"
               f"    {'base address':18}: {self._base_address}\n"
               f"    {'volume size':18}: {self.volume_size}\n"
               f"    {'log offset':18}: {self.log_offset}\n"
               f"    {'log size':18}: {self.log_size}\n"
               f"    {'data offset':18}: {self.data_offset}\n"
               f"    {'data size':18}: {self.data_size}\n"
               f"    {'# of data records':18}: {self.data_number}\n"
               f"    {'tree1 offset':18}: {self.tree1_offset}\n"
               f"    {'tree1 size':18}: {self.tree1_size}\n"
               f"    {'tree2 offset':18}: {self.tree2_offset}\n"
               f"    {'tree2 size':18}: {self.tree2_size}\n"
               f">"
        )
