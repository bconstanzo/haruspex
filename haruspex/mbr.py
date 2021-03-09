"""
Module to parse Master Boot Record partition tables and return a (reasonably)
sane object.
"""
# TODO: add EBR support
# TODO: add comparisson operators for the classes?
#       this just came up after a small refactoring, and it'd be a simpler way
#       to test things
import struct


class Partition:
    """Handles one entry in the MBR table."""
    partition_types = {
        0x00: "Empty",
        0x01: "FAT12 CHS",
        0x04: "FAT16 CHS",
        0x05: "Microsoft Extended",
        0x06: "FAT16 CHS 32MB",
        0x07: "NTFS",
        0x0b: "FAT32 CHS",
        0x0c: "FAT32 LBA",
        0x0e: "FAT16 LBA 2GB",
        0x0f: "Microsoft Extended LBA",
    }   # this dict could be extended to include more types

    def __init__(self, data=bytes(16), *, 
                 bootable=None, chs_start=None, type=None, chs_end=None,
                 start=None, size=None
        ):
        """
        :param data: raw bytes for the MBR record, at least 16 bytes long
        """
        def _chs(value):
            """A little helper for CHS parsing."""
            head, sector, cylinder = struct.unpack("<3B", value)
            cylinder = ((sector & 0b11000000) << 2) | cylinder
            sector   =   sector & 0b00111111
            return (cylinder, head, sector)

        p_bootable  = data[0]
        p_chs_start = _chs(data[1:4])
        p_type      = data[4]
        p_chs_end   = _chs(data[5:8])
        p_start,    = struct.unpack("<I", data[8:12])
        p_size,     = struct.unpack("<I", data[12:16])
        # and now we set, either the overridden values or the parsed ones
        self._raw_data = data
        self.bootable  = bootable or p_bootable
        self.chs_start = chs_start or p_chs_start
        self.type      = type or p_type
        self.chs_end   = chs_end or p_chs_end
        self.start     = start or p_start
        self.size      = size or p_size
    
    def __bytes__(self):
        """
        Handles packing the partitions attributes into the binary struct that
        is saved to disk.
        """
        def _chs(cylinder, head, sector):
            sector   = ((cylinder & 0b1100000000) >> 2) | (sector & 0b00111111)
            cylinder =   cylinder & 0b0011111111
            # just in case, let's clip the values
            cylinder = min(max(0, cylinder), 255)
            head     = min(max(0, head), 255)
            sector   = min(max(0, sector), 255)
            return (cylinder, head, sector)
        
        start_c, start_h, start_s = _chs(*self._chs_start)
        end_c  , end_h,   end_s   = _chs(*self._chs_end)
        return struct.pack(
            "<BBBBBBBBII",
            self._bootable,
            start_h, start_s, start_c,
            self._type,
            end_h, end_s, end_c,
            self._start,
            self._size
        )
    
    def __repr__(self):
        ret = f"< Partition - {self.type} - boot: {self.bootable} @ {self.start} of {self.size} >"
        return ret
    
    @property
    def bootable(self):
        """
        Bootable flag for the partition.

        When setting this property, the boolean value (or expression) passed is
        used to determine the correct bytes to store on disk.
        """
        return self._bootable == 0x80
    
    @bootable.setter
    def bootable(self, value):
        if value:
            self._bootable = 0x80
        else:
            self._bootable = 0x0
    
    @property
    def chs_start(self):
        """
        Cylinder-Head-Sector start address. Parsed at initialization time.

        Read only.
        """
        return self._chs_start
    
    @chs_start.setter
    def chs_start(self, value):
        self._chs_start = value
    
    @property
    def type(self):
        """
        Partition type. The getter returns a string coded in the
        Partition.partition_types dict. Partition._type holds the underlying int
        value.

        The setter clips any integer value given to the 0..255 range.
        """
        return self.partition_types.get(self._type, "Unknown")
    
    @type.setter
    def type(self, value):
        value = int(value)
        value = min(max(0, value), 255)  # clip it to 0..255
        self._type = value
    
    @property
    def chs_end(self):
        """
        Cylinder-Head-Sector end address. Parsed at initialization time.

        Read only.
        """
        return self._chs_end
    
    @chs_end.setter
    def chs_end(self, value):
        self._chs_end = value

    @property
    def start(self):
        """
        LBA start address. Parsed at initialization time. The setter enforces a
        0x0..0xffffffff range.
        """
        return self._start
    
    @start.setter
    def start(self, value):
        value = int(value)
        value = min(max(0, value), 0xffffffff)
        self._start = value
    
    @property
    def size(self):
        """
        Parition size. Parsed at initialization time. The setter enforces a
        0x0..0xffffffff range.
        """
        return self._size
    
    @size.setter
    def size(self, value):
        value = int(value)
        value = min(max(0, value), 0xffffffff)
        self._size = value
    
    def to_bytes(self):
        return bytes(self)


class Table:
    """
    Handles one Master Boot Record (simple case without Extended Partitions).
    """
    def __init__(self, data=bytes(512), *,
                 boot_code=None, partitions=None
        ):
        """
        :param data: raw bytes read from an MBR (at least 512 bytes long)
        """
        self._raw_data = data
        data = data[446:]
        p_boot_code = self._raw_data[:446]
        p_parts = filter(
            lambda x: x != b"\x00" * 16,  # filter out empty partitions
            (data[i * 16: i * 16 + 16] for i in range(4))
        )
        p_partitions = [Partition(p) for p in p_parts]
        # this implementation is "good enough", but not thorough
        # -- the legacy files have a larger implementation that includes
        #    extended partitions parsing
        # override parsed values with keyword-only arguments
        self.boot_code = boot_code or p_boot_code
        self.partitions = partitions or p_partitions

    def __bytes__(self):
        ret = bytearray(512)
        ret[:446] = self.boot_code
        parts = b"".join(bytes(p) for p in self.partitions)
        parts = parts[:64]
        psize = len(parts)
        ret[446: 446 + psize] = parts
        ret[510: 512] = b"\x55\xaa"
        return bytes(ret)
    
    def __repr__(self):
        ret  = [f"< MBR Partition Table @ {id(self)} >"]
        ret.extend(
               [f"    {p}" for p in self.partitions]
        )
        return "\n".join(ret)

    def to_bytes(self):
        return bytes(self)
