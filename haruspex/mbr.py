import struct


class Record:
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
        self.bootable  = False
        self.chs_start = (0x0, 0x0, 0x0)
        self.type      = 0x0
        self.chs_end   = (0x0, 0x0, 0x0)
        self.lba_start = 0x0
        self.size      = 0
        # after setting the attributes for the instance, we parse the raw data
        self._parse()
    
    def __repr__(self):
        ret = "< Partition - {type} - boot: {bootable} @ {lba_start} of {size} >"
        return ret.format_map(self.__dict__)
    
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
        self.bootable   = data[0] == 0x80
        # CHS addresses should be 0 in any recent MBR, stil...
        self.chs_start  = _chs(data[1:4])
        self.type       = self.partition_types.get(data[4], "Unknown")
        self.chs_end    = _chs(data[5:8])
        self.lba_start, = struct.unpack("<I", data[8:12])
        self.size,      = struct.unpack("<I", data[12:16])


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
        ret  = [f"< Partition Table @ {id(self)} >"]
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
        self.partitions = [Record(p) for p in p_parts]
        # this implementation is "good enough", but not thorough
        # -- the legacy files have a larger implementation that includes
        #    extended partitions parsing

