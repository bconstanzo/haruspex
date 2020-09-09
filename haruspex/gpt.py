"""
Module to parse GUID Partition Tables.
"""
import struct


from .guid import GUID
from .utils import slicer


class Partition:
    """GPT Partition Record"""
    partition_types = {
        # we have to fill in a few GUIDs here...
        # the only sane list we've found already is here:
        # * http://www.liquisearch.com/guid_partition_table/partition_type_guids
        GUID("C12A7328-F81F-11D2-BA4B-00A0C93EC93B"): "EFI System Partition",
        # Microsoft GUID types
        GUID("DE94BBA4-06D1-4D40-A16A-BFD50179D6AC"): "Windows Recovery Tools Partition",
        GUID("E3C9E316-0B5C-4DB8-817D-F92DF00215AE"): "Microsoft Reserved Partition",
        GUID("EBD0A0A2-B9E5-4433-87C0-68B6B72699C7"): "Basic Data Partition",
    }

    def __init__(self, data, length):
        """
        :param data: raw bytes of the partition record
        :param length: length in bytes of the partition record, defaults to 128
        """
        self._raw_data = data
        self.guid_type = GUID(bytes(16), mixed_endian=True)
        self.guid_part = GUID(bytes(16), mixed_endian=True)
        self.type      = ""
        self.start     = 0
        self.end       = 0
        self.flags     = 0
        self.name      = ""
        # now for something extra (and not completely different)
        self.size      = 0  # we define it for ease of use
        self._length   = length
        self._parse()
    
    def __repr__(self):
        ret = "< Partition - {type} - @ {start} of {size} >"
        return ret.format_map(self.__dict__)
    
    def _parse(self):
        data   = self._raw_data
        length = self._length - 56  # this is the length of the name field
        start, end, flags = struct.unpack("<QQQ", data[32:56])
        name, = struct.unpack(f"{length}s", data[56:])
        name  = name.decode("utf-16")
        if "\x00" in name:
            name = name[:name.find("\x00")]
        self.guid_type = GUID(data[ 0:16], mixed_endian=True)
        self.guid_part = GUID(data[16:32], mixed_endian=True)
        self.type      = self.partition_types.get(self.guid_type, "Unknown")
        self.start     = start
        self.end       = end
        self.size      = end - start + 1
        self.name      = name


class Table:
    """GPT Partition Table"""
    def __init__(self, raw_data):
        self._raw_data = raw_data
        rev, hsize, crc32, _res, cur_lba, back_lba, first_lba, last_lba \
            = struct.unpack("<LLLLQQQQ", raw_data[8:56])
        # disk GUID comes in the middle here...
        parts_lba, parts_num, parts_size, crc32_parts = struct.unpack("<QLLL", raw_data[72:92])
        self.signature   = raw_data[0:8]
        self.revision    = rev
        self.header_size = hsize
        self.current_lba = cur_lba
        self.backup_lba  = back_lba
        self.first_lba   = first_lba
        self.last_lba    = last_lba
        self.disk_guid   = GUID(raw_data[56:72], mixed_endian=True)
        self.parts_lba   = parts_lba
        self.parts_num   = parts_num
        self.parts_size  = parts_size
        self.crc32_parts = crc32_parts
        self.partitions  = []
        self._parse()
    
    def __repr__(self):
        ret  = [f"< GUID Partition Table @ {id(self)} >"]
        ret.extend(
               [f"    {p}" for p in self.partitions]
        )
        return "\n".join(ret)
    
    def __str__(self):
        ret = [
            f"< GPT Partition Table @ {id(self)} >",
            f"    signature: {str(self.signature):>20}",
            f"     revision: {str(self.revision):>20}",
            f"  header size: {str(self.header_size):>20}",
            f"  current LBA: {str(self.current_lba):>20}",
            f"   backup LBA: {str(self.backup_lba):>20}",
            f"    first LBA: {str(self.first_lba):>20}",
            f"     last LBA: {str(self.last_lba):>20}",
            f"    disk GUID: {str(self.disk_guid):>20}",
            f"    parts LBA: {str(self.parts_lba):>20}",
            f"      parts #: {str(self.parts_num):>20}",
            f"   parts size: {str(self.parts_size):>20}",
        ]
        return "\n".join(ret)
    
    def _parse(self):
        """
        This method parses the partition entries in the following LBAs, 
        """
        part_data = self._raw_data[512: 512 + 16384]  # should be this length...
        size      = self.parts_size
        self.partitions = [
            Partition(s, size)
            for s in slicer(part_data, size)
            if s != bytes(size)
        ]
