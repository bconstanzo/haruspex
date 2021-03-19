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

    def __init__(self, data=bytes(128), length=128, *,
                 guid_type=None, guid_part=None, start=None, end=None,
                 size=None, flags=None, name=None
        ):
        """
        :param data: raw bytes of the partition record
        :param length: length in bytes of the partition record, defaults to 128
        """
        self._raw_data = data
        self._length   = length
        # now for something extra (and not completely different)
        data   = self._raw_data
        nlength = self._length - 56  # this is the length of the name field
        p_guid_type = GUID(data[ 0:16], mixed_endian=True)
        p_guid_part = GUID(data[16:32], mixed_endian=True)
        p_start, p_end, p_flags = struct.unpack("<QQQ", data[32:56])
        p_name, = struct.unpack(f"{nlength}s", data[56:])
        p_name  = p_name.decode("utf-16")
        if "\x00" in p_name:
            p_name = p_name[:p_name.find("\x00")]
        # and now we set the values, parsed or given
        self.guid_type = guid_type or p_guid_type
        self.guid_part = guid_part or p_guid_part
        self.type      = self.partition_types.get(self.guid_type, "Unknown")  # make property
        self.start     = start or p_start
        self.end       = end or p_end
        self.size      = self.end - self.start + 1
        self.name      = name or p_name
    
    def __repr__(self):
        ret = "< Partition - {type} - @ {start} of {size} >"
        return ret.format_map(self.__dict__)


class Table:
    """GPT Partition Table"""
    def __init__(self, raw_data, *,
                 signature=None, revision=None, header_size=None,
                 current_lba=None, backup_lba=None, first_lba=None,
                 last_lba=None, disk_guid=None, parts_lba=None, parts_num=None,
                 parts_size=None, crc32_parts=None, partitions=None
        ):
        """

        """
        self._raw_data = raw_data
        p_rev, p_hsize, p_crc32, _res, p_cur_lba, p_back_lba, p_first_lba, p_last_lba \
            = struct.unpack("<LLLLQQQQ", raw_data[8:56])
        # disk GUID comes in the middle here...
        p_parts_lba, p_parts_num, p_parts_size, p_crc32 = struct.unpack("<QLLL", raw_data[72:92])
        # and now we set them all...
        self.signature   = signature or raw_data[0:8]
        self.revision    = revision or p_rev
        self.header_size = header_size or p_hsize
        self.current_lba = current_lba or p_cur_lba
        self.backup_lba  = backup_lba or p_back_lba
        self.first_lba   = first_lba or p_first_lba
        self.last_lba    = last_lba or p_last_lba
        self.disk_guid   = disk_guid or GUID(raw_data[56:72], mixed_endian=True)
        self.parts_lba   = parts_lba or p_parts_lba
        self.parts_num   = parts_num or p_parts_num
        self.parts_size  = parts_size or p_parts_size
        self.crc32_parts = crc32_parts or p_crc32
        part_data = raw_data[512: 512 + 16384]  # should be this length...
        p_partitions = [
            Partition(s, self.parts_size)
            for s in slicer(part_data, self.parts_size)
            if s != bytes(self.parts_size)
        ]
        self.partitions  = partitions or p_partitions
    
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
