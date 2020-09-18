"""
Module to parse Master Boot Record partition tables and return a (reasonably)
sane object.
"""
# TODO: add EBR support
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

    def __init__(self, data):
        """
        :param data: raw bytes for the MBR record, at least 16 bytes long
        """
        self._raw_data = data
        self._bootable  = 0x0
        self._chs_start = (0x0, 0x0, 0x0)
        self._type      = 0x0
        self._chs_end   = (0x0, 0x0, 0x0)
        self._start     = 0x0
        self._size      = 0
        # after setting the attributes for the instance, we parse the raw data
        self._parse()
    
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
    
    def _parse(self):
        """
        Parses self._raw_data and uses it to modifiy/complete the internal state
        of Record.
        """
        def _chs(value):
            head, sector, cylinder = struct.unpack("<3B", value)
            cylinder = ((sector & 0b11000000) << 2) | cylinder
            sector   =   sector & 0b00111111
            return (cylinder, head, sector)

        data = self._raw_data
        self._bootable  = data[0]
        # CHS addresses should be 0 in any recent MBR, stil...
        self._chs_start = _chs(data[1:4])
        self._type      = data[4]
        self._chs_end   = _chs(data[5:8])
        self._start,    = struct.unpack("<I", data[8:12])
        self._size,     = struct.unpack("<I", data[12:16])
    
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
            self.bootable = 0x0
    
    @property
    def chs_start(self):
        """
        Cylinder-Head-Sector start address. Parsed at initialization time.

        Read only.
        """
        return self._chs_start
    
    @chs_start.setter
    def chs_start(self, value):
        pass
    
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
    def chs_start(self, value):
        pass

    @property
    def start(self):
        """
        LBA start address. Parsed at initialization time. The setter enforces a
        0x0..0xffffffff range.
        """
        return self._start
    
    @start.setter
    def start(self, value):
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
        value = min(max(0, value), 0xffffffff)
        self._size = value
    
    def to_bytes(self):
        return bytes(self)


class Table:
    """
    Handles one Master Boot Record (simple case without Extended Partitions).
    """
    def __init__(self, data):
        """
        :param data: raw bytes read from an MBR (at least 512 bytes long)
        """
        self._raw_data = data
        self.partitions = []
        self._parse()
    
    def __repr__(self):
        ret  = [f"< MBR Partition Table @ {id(self)} >"]
        ret.extend(
               [f"    {p}" for p in self.partitions]
        )
        return "\n".join(ret)
    
    def _parse(self):
        """
        Parses the raw data passed during initialization. Does not return, but
        changes the self.partitions list.
        """
        data = self._raw_data[446:]
        p_parts = filter(
            lambda x: x != b"\x00" * 16,  # filter out empty partitions
            (data[i * 16: i * 16 + 16] for i in range(4))
        )
        self.partitions = [Partition(p) for p in p_parts]
        # this implementation is "good enough", but not thorough
        # -- the legacy files have a larger implementation that includes
        #    extended partitions parsing

