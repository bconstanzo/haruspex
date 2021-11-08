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
