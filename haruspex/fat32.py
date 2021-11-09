"""
This module handles reading from and writing to a FAT32 filesystem.
"""
import calendar
import datetime
import struct
import sys


from .utils import slicer


# TODO: read https://stackoverflow.com/questions/13775893/converting-struct-to-byte-and-back-to-struct
#       and research a bit into this being a reasonable way to convert bytes
#       into structs (and back).
# TODO: consider widening support for other encodings (eg: latin1, utf-8, etc)
#       in file/directory names.
# TODO: Linux-style LFN support (see https://lkml.org/lkml/2009/6/26/314)     


ATTRIBUTES = {
    "read-only": 0x01, 
    "hidden"   : 0x02,
    "system"   : 0x04,
    "volume-id": 0x08,
    "directory": 0x10,
    "archive"  : 0x20,
}

# TODO: this is actually a hack right now, and there might be a simpler way to
#       do it
ALL_ASCII = b"".maketrans(b"", b"")  # a bit hacky, but works
FILENAME_CHARS = b"0123456789 ABCDEFGHIJKLMNOPQRSTUVWXYZ!#$%&'()-@^_`{}~\xe5"
REMAIN_ASCII = ALL_ASCII
for idx, char in enumerate(FILENAME_CHARS):
    char = FILENAME_CHARS[idx:idx + 1]
    REMAIN_ASCII = REMAIN_ASCII.replace(char, b"")
FILENAME_TRANS = b"".maketrans(
    REMAIN_ASCII,
    b"\x00" * len(REMAIN_ASCII)
)
# TODO: the whole PATH_SEP thing might need better thought, but for the moment
#       simple should be enough
PATH_SEP = "\\"


def read_attributes(value):
    """
    Receives the raw attributes byte, and parses it into a dictionary based on
    the `ATTRIBUTES` constant.

    :param raw_attrs: bytes object, only the first byte is used
    :return: dictionary with the corresponding attributes and their bool value
    """
    ret = {}
    for k, v in ATTRIBUTES.items():
        ret[k] = bool(value & v)
    return ret


def read_time(bytes_, mili=0):
    """
    Receives time + date bytes in `bytes_`, and returns a datetime object.
    Checks for pathological 0xffff patterns.

    :param bytes_: raw value, made from the the time+date fields in the raw
        directory entry/file record.
    :param mili: the raw byte (int) that encodes the 10 milisecond precision,
        for timestamps that support it (defaults to 0)
    :return: datetime.datetime object
    """
    raw_time, raw_date, = struct.unpack("<HH", bytes_)
    # first we take care of the date
    year    = (raw_date >> 9) + 1980
    month   = (raw_date & 0b0000000111100000) >> 5
    day     =  raw_date & 0b0000000000011111
    # and now the time
    hour    =  raw_time >> 11
    minute  = (raw_time & 0b0000011111100000) >> 5
    second  = (raw_time & 0b0000000000011111) * 2
    second += mili // 100
    micros  = (mili % 100) * 10000
    # we know theres an issue in some Linux based systems that make
    # 0xffffffff datetimes for some FileRecords (that don't seem to belong to
    # the files, some kind of temporary record) so we must check a few things:
    year   = max(1980,  min(2107,    year))  # clips the values to within range
    month  = max(1,     min(12,     month))
    _weeks, max_days = calendar.monthrange(year, month)
    day    = max(1,     min(max_days, day))
    hour   = min(23,   hour)
    minute = min(59, minute)
    second = min(59, second)
    # that gives a few sanity checks and should catch that particular issue
    dt = datetime.datetime(year, month, day, hour, minute, second, micros)
    return dt


class FileRecord:
    """
    An entry inside a FAT32 directory.
    """
    def __init__(self, data):
        self._raw_data   = data
        self._name       = b""
        self._ext        = b""
        self._size       = -1
        self._attributes = {k: False for k in ATTRIBUTES}
        self._flags      = 0  # reserved, should be 0 but different implementations may use it 
        self._cluster    = -1
        self._created    = None
        self._last_access= None
        self._modified   = None
        # that's all for real attributes of a file record
        self._parse()
    
    # The Properties
    # (these could be done with metaclasses, but...)
    @property
    def raw_data(self):
        """
        The raw bytes used to initialize the File Record. Read only for now.
        """
        return self._raw_data
    
    @raw_data.setter
    def raw_data(self, value):
        pass  # let's make it read-only for the moment

    @property
    def name(self):
        """
        The name of the File Record.

        When setting this property, checks are made to make sure it can be
        represented as the packed structure on disk.
        """
        return self._name
    
    @name.setter
    def name(self, value):
        if isinstance(value, str):
            value = bytes(value, "latin1")
        value = value.upper()  # not supporting long names for the moment
        name = value.translate(FILENAME_TRANS)
        name = name.replace(b"\x00", b"")
        name = name[0:8]   # byebye long names!
        # let's check if there's an ext, for the lazy user
        if b"." in value:
            name, dot, ext = value.rpartition(b".")
            ext = ext.rstrip()
            self._ext = ext[-3:]
        name = name.rstrip()
        self._name = name # 
        # will not enforce name uniqueness, just being uppercase and within
        # valid range of characters
    
    @property
    def ext(self):
        """
        The extension of the File Record.

        When setting this property, checks are made to make sure it can be
        represented as the packed structure on disk.
        """
        return self._ext
    
    @ext.setter
    def ext(self, value):
        if isinstance(value, str):
            value = bytes(value, "latin1")
        value = value.upper()
        ext = value.translate(FILENAME_TRANS)
        ext = ext.replace(b"\x00", b"")
        ext = ext.rstrip()
        ext = ext[0:3]
        self._ext = ext
    
    @property
    def fullname(self):
        """
        Helper property, returns name for directories and name.ext for files.
        Read only.
        """
        if self.attributes["directory"]:
            return self.name
        return self.name + b"." + self.ext
    
    @fullname.setter
    def fullname(self, value):
        pass
    
    @property
    def size(self):
        """
        The size of the File Record.

        When setting this property, checks are made to make sure it can be
        represented as the packed structure on disk. Values larger than
        0xffffffff are truncated at it.
        """
        return self._size
    
    @size.setter
    def size(self, value):
        if value > 0xffffffff:
            value = 0xffffffff
        self._size = value
    
    @property
    def attributes(self):
        """
        The attributes of the File Record.

        When setting this property, checks are made to make sure it can be
        represented as the packed structure on disk.
        """
        return self._attributes
    
    @attributes.setter
    def attributes(self, value):
        # let's cleanup in case the given dict has some extra keys
        value = {k:v for k, v in value.items() if k in ATTRIBUTES}
        self._attributes.update(value)
    
    @property
    def flags(self):
        """
        The flags of the File Record. Read only.

        This is actually a reserved field, which non-Microsoft implementations
        use for different purposes.
        """
        return self._flags
    
    @flags.setter
    def flags(self, value):
        self._flags = value  # we're gonna need this for the optional arguments

    @property
    def cluster(self):
        """
        The first cluster of the File Record.

        When setting this property, checks are made to make sure it can be
        represented as the packed structure on disk. Same as with size, we
        simply check for the value to fit in a uint32. The filesystem should
        be responsible to check that the referenced cluster is valid and not
        out of range.
        """
        return self._cluster
    
    @cluster.setter
    def cluster(self, value):
        if value > 0xffffffff:
            value = 0xffffffff
        # no point in checking anything else, the filesystem should make
        # sure there's no invalid cluster set
        self._cluster = value
    
    @property
    def created(self):
        """
        The creation timestamp of the File Record.

        When setting this property, checks are made to make sure it can be
        represented as the packed structure on disk. Those are:

        * Year is set to be in range 1980-2107 (truncated at those values for
          smaller/larger).
        * Microsecond accuracy of the datetime object is capped to 10ms
          resolution (as can be represented in structure)
        """
        return self._created
    
    @created.setter
    def created(self, value):
        # truth is, python's datetime object handles a lot already
        # so we only need to check the year
        year = value.year
        if year < 1980:
            year = 1980
            value = value.replace(year=year)
        elif year > 2107:
            year = 2107
            value = value.replace(year=year)
        micros = value.microsecond
        micros = (micros // 10000) * 10000  # let's be honest about the precision
        value.replace(microsecond=micros)
        self._created = value

    # last_access
    @property
    def last_access(self):
        """
        The last accessed timestamp of the File Record.

        When setting this property, checks are made to make sure it can be
        represented as the packed structure on disk. Those are:

        * Year is set to be in range 1980-2107 (truncated at those values for
          smaller/larger).
        * Since the structure only has 2 bytes for a date, the datetimes object
          hour, minut, second and microsecond are set to 0.
        
        It is technically a datetime still to be consistent with the other
        timestamps.
        """
        return self._last_access
    
    @last_access.setter
    def last_access(self, value):
        # truth is, python's datetime object handles a lot already
        # so we only need to check the year
        year = value.year
        if year < 1980:
            year = 1980
            value = value.replace(year=year)
        elif year > 2107:
            year = 2107
            value = value.replace(year=year)
        # and here we erase the time
        value = value.replace(hour=0, minute=0, second=0, microsecond=0)
        # technically a date object at this point, but we prefer to keep
        # things consistent and have them all be datetime
        self._last_access = value

    @property
    def modified(self):
        """
        The modified timestamp of the File Record.

        When setting this property, checks are made to make sure it can be
        represented as the packed structure on disk. Those are:

        * Year is set to be in range 1980-2107 (truncated at those values for
          smaller/larger).
        * The datetimes object second resolution is cut to 2 second icnrementes
          (as the on-disk structure allows) and microseconds are set to 0.
        """
        return self._modified
    
    @modified.setter
    def modified(self, value):
        # truth is, python's datetime object handles a lot already
        # so we only need to check the year
        year = value.year
        if year < 1980:
            year = 1980
            value = value.replace(year=year)
        elif year > 2107:
            year = 2107
            value = value.replace(year=year)
        second = value.second
        second = (second // 2) * 2  # let's be honest about the precision
        value = value.replace(second=second, microsecond=0)
        self._modified = value
    
    @property
    def deleted(self):
        """
        Boolean for the FileRecord being marked as deleted.

        Setting this property to True (or True-like values) re-writes the first
        character the FileRecord's name attribute. Setting it to false checks
        for a \\xe5 value on the first byte, and if it finds it, replaces it for
        and underscore.
        """
        return self._name[0:1] == b"\xe5"
    
    @deleted.setter
    def deleted(self, value):
        if value:
            self._name = b"\xe5" + self._name[1:]
        else:
            if self._name[0:1] == b"\xe5":
                self._name = b"_" + self._name[1:]
    
    def __repr__(self):
        name = self.name.decode("latin1")
        ext  = self.ext.decode("latin1")
        if self.attributes["directory"]:
            showname = f"<DIR> {name}"
        else:
            showname = f"{name}.{ext}"
        return f"< DirectoryEntry: {showname}>"
    
    def __str__(self):
        name = self.name.decode("latin1")
        ext  = self.ext.decode("latin1")
        if self.attributes["directory"]:
            showname = f"<DIR> {name}"
        else:
            showname = f"{name}.{ext}"
        return (
               f"< DirectoryEntry: {showname}\n"
               f"    {'size':12}:{self.size:>12}\n" 
               f"    {'attributes':12}:{self._attrs2str():>12}\n" 
               f"    {'cluster':12}:{self.cluster:>12}\n" 
               f"    {'created':12}: {self.created}\n" 
               f"    {'last_access':12}: {self.last_access}\n" 
               f"    {'modified':12}: {self.modified}\n" 
               f"    {'deleted':12}:{str(self.deleted):>12}\n" 
               f">"
        )
    
    def _attrs2str(self):
        """
        Helper function for pretty-printing the attributes in __str__.
        """
        ret = [
            k[0].upper() if v else k[0]
            for (k, v) in self._attributes.items()
        ]
        return "".join(ret)
    
    def _parse(self):
        """
        Parses self._raw_data and updates the properties of the file.
        """
        # TODO: maybe it should be called load? or just parse?
        #       will define it better after having a dump() or save() method
        self.name        = self._raw_data[0:8] + b"." + self._raw_data[8:11]
        # we use the shorthand that sets name and extension in a single pass
        self.size,       = struct.unpack("<L", self._raw_data[28:32])
        self.attributes  = read_attributes(self._raw_data[11])
        self.flags       = self._raw_data[12]
        self.cluster,    = struct.unpack("<L", self._raw_data[26:28] + self._raw_data[20:22])
        self.created     = read_time(self._raw_data[14:18], mili=self._raw_data[13])
        self.last_access = read_time(b"\x00\x00" + self._raw_data[18:20])
        self.modified    = read_time(self._raw_data[22:26])



class Directory:
    """
    Class to handle the abstraction for reading (eventually writing/modifying)
    a directory/folder in a FAT32 filesystem. As with FileHande, this class is
    strange, because it's more involved than you'd usually find, and has to
    take care of some things which are usually responsibility of the OS.

    :param filesystem: the base filesystem (of class FAT32) to which the
        Directory belongs
    :param record: the FileRecord (Directory Entry) for the directory
    :param parent: (Directory) parent of the (new) directory, used to build a
        path string
    :return: Directory object in `filesystem `for the given `record`
    """
    def __init__(self, filesystem, record, *, parent=None):
        self._filesystem = filesystem
        if record is None:
            record = FileRecord(bytes(32))
            record.cluster = filesystem.root_cluster
        self._record = record
        self.cluster = record.cluster
        # a bit of a hack for the root cluster
        self._parent     = parent
        self.files       = []
        if parent is None:
            self.path = record.name.decode("latin1")
        else:
            self.path = parent.path + PATH_SEP + record.name.decode("latin1")
        self._parse()
    
    def __repr__(self):
        return f"< Directory {self.path}>"
    
    def __str__(self):
        ret =  f"< Directory {self.path}\n"
        ret += "  Files: [\n    "
        ret += "\n    ".join([repr(f) for f in self.files])
        ret += "\n  ]"
        ret += "\n>"
        return ret
    
    def _parse(self):
        """
        Parses the directory cluster on disk, creating the FileRecords for every
        entry in the directory (wink). For the moment long file names (LFNs) are
        skipped since we don't want to tread into Microsoft patents territory.
        Might think of supporting Linux-stlye LFNs.
        """
        
        def lfn_filter(record):
            """
            Returns false for records which are LFN data.
            """
            attrs = record.attributes
            lfn = (
                attrs["read-only"] and
                attrs["hidden"] and
                attrs["system"] and
                attrs["volume-id"]
            )
            return not(lfn)

        filesystem   = self._filesystem
        record       = self._record
        raw_data     = []
        cluster      = self.cluster
        next_cluster = filesystem.fat1[cluster]
        while next_cluster <= 0x0ffffff0:
            raw_data.append(filesystem._read_cluster(cluster))
            cluster = next_cluster
            next_cluster = filesystem.fat1[cluster]
        raw_data.append(filesystem._read_cluster(cluster))
        raw_data  = b"".join(raw_data)
        self.files = list(filter(
            lfn_filter,
            (
                FileRecord(s)
                for s in slicer(raw_data, 32)
                if s != bytes(32)
            )
        ))

class FileHandle:
    """
    Class to handle reading (and eventually writing) files in the FAT32
    filesystem. This class is a lot more involved than pythons standard file
    object, because it actually deals with the filesystem on a level closer to
    the OS.
    """
    def __init__(self, filesystem, record, mode="rb", *, parent=None):
        self._filesystem = filesystem
        self._record     = record
        self._mode       = mode
        if parent is None:
            self.path = (record.name + b"." + record.ext).decode("latin1")
        else:
            self.path = parent.path + PATH_SEP + (record.name + b"." + record.ext).decode("latin1")
        # this is all a lie (yet), we'll just open in "rb" mode
        # we will try to mimic the IOBase methods as close as possible, without
        # going crazy in it... right?
        self.closed       = False
        # and we'll need a few other attributes as well
        self._buffer      = bytearray(filesystem._read_cluster(record.cluster))
        self._buffer_pos  = 0  # for easier handling of the buffer and _file_pos
        self._buffer_size = filesystem.sectors_per_cluster * filesystem.bytes_per_sector
            # we buffer a cluster at a time
        self._ccluster    = record.cluster
        # we keep track of which cluster we're own to read the next one when
        # necessary
        self._file_pos    = 0  # position in the file, .tell() returns this
        self._readable    = True  # will set along with mode, when supported
    
    def __repr__(self):
        return f"< FileHandle for {self.path} >"
    
    def __str__(self):
        return self.__repr__()

    def __del__(self):
        # should probably do something about writing, for example
        # and flusihing changes to disk
        # once writing is supported, that is
        pass
    
    def close(self):
        """
        Closes the file.
        """
        self.closed = True
    
    def fileno(self):
        pass

    def flush(self):
        pass

    def isatty(self):
        return False
    
    def read(self, size=-1):
        bsize = self._buffer_size
        start = self._buffer_pos
        if size < 0:
            size = self._record.size - self._file_pos
        ret = []
        # and now we read
        while (bsize - start) < size:  # we have to read clusters from the chain
            ret.append(self._buffer[start:])
            size -= (bsize - start)
            self._file_pos += (bsize - start)
            ncluster = self._filesystem.fat1[self._ccluster]
            if ncluster >= 0x0ffffff0:
                # magic EOF cluster number, found by trial and error
                # TODO: check that the cluster is within bounds of the fs
                break
            start = 0
            self._ccluster = ncluster
            self._buffer = bytearray(self._filesystem._read_cluster(ncluster))
        span = min(self._record.size - self._file_pos, size)
        ret.append(self._buffer[start: start + span])
        self._buffer_pos =  start + span
        self._file_pos   += span
        return b"".join(ret)
    
    def readable(self):
        """
        Returns whether the file is readable or not.
        """
        return self._readable
    
    def readlines(self, hint=-1):
        pass  # not ready to implement this yet

    def seek(self, offset, whence=0):
        """
        Moves the file pointer to offset.

        :param offset: position to move the file pointer
        :param whence: not implemented (yet)
        :return: the current position of the file pointer, after moving (will
            be equal to `offset`, unless something goes very wrong)
        """
        filesystem = self._filesystem
        record     = self._record
        bsize      = self._buffer_size
        # it's not pretty but it's simple -- we'll have to do a scan of the
        # FAT to see in which cluster we have to land, and buffer that
        # c_idx will be our cluster index
        c_idx = offset // bsize
        self._ccluster = record.cluster
        ncluster = self._filesystem.fat1[self._ccluster]
        while (ncluster < 0x0ffffff0) and c_idx > 0:
            self._ccluster = ncluster
            c_idx -= 1
            ncluster = self._filesystem.fat1[self._ccluster]
        if offset >= record.size:  # we went over the end of the file
            self._buffer     = bytearray(filesystem._read_cluster(self._ccluster))
            self._file_pos   = record.size
            self._buffer_pos = record.size % bsize
            return self._file_pos
        self._buffer     = bytearray(filesystem._read_cluster(self._ccluster))
        self._buffer_pos = offset % bsize
        self._file_pos   = offset
        return self._file_pos
    
    def seekable(self):
        return True  # hardcoded for now, can't think a situation where it won't be
    
    def tell(self):
        """
        Returns the current position of the file pointer.
        """
        return self._file_pos
    
    def truncate(self, size=None):
        pass
        # will think about implementing this
    
    def writeable(self):
        return False  # hardcoded, will work on this later
    
    def writelines(self, lines):
        pass  # dummy method, for the moment


class FAT32:
    """
    Class that gathers methods and objects to handle a FAT32 filesystem.
    """
    def __init__(self, handle, base_address=0):
        """
        FAT32 instance.

        :param handle: 'rb' or 'rb+' file-like object that holds a FAT32
            filesystem
        :param base_address: byte offset of the FAT32 filesystem in `handle`
            (defaults to 0, you'll most certainly want to provide a value)
        """
        self._base_address = base_address
        self._handle       = handle
        self._handle.seek(base_address)
        # and now for the header data...}
        buffer = self._handle.read(512)
        bps, spc, rs, nof = struct.unpack("<HBHB", buffer[0x0b:0x11])
        spf, _, rc = struct.unpack("<LLL", buffer[0x24:0x30])
        self.bytes_per_sector    = bps
        self.sectors_per_cluster = spc
        self.reserved_sectors    = rs
        self.number_of_fats      = nof
        self.sectors_per_fat     = spf
        self.root_cluster        = rc
        self.root                = None  # we set its value later
        # and now some calculations...
        self.fat1_address = rs * bps
        self.fat2_address = (rs + spf) * bps
        self.base_cluster_address = (rs + (nof * spf)) * bps
        # for all these addresses we have to add the base_address of the
        # filesystem, otherwise we'll read anywhere on the device/image
        self.fat1_address += base_address
        self.fat2_address += base_address
        self.base_cluster_address += base_address
        # and now we're set!
        # I should probably set these to be read only through properties...
        self.fat1 = []
        self.fat2 = []
        self._load_fats()
        self._post_init()
    
    def __repr__(self):
        return f"< FAT32 @ {self._base_address} >"
    
    def __str__(self):
        return (
               "< FAT32 Filesystem:\n"
               f"    {'base address':24}: {self._base_address}\n"
               f"    {'sectors per cluster':24}: {self.sectors_per_cluster}\n"
               f"    {'reserved sectors':24}: {self.reserved_sectors}\n"
               f"    {'number of FATs':24}: {self.number_of_fats}\n"
               f"    {'sectors per FAT':24}: {self.sectors_per_fat}\n"
               f"    {'root cluster':24}: {self.root_cluster}\n"
               f"    {'FAT1 address':24}: {self.fat1_address}\n"
               f"    {'FAT2 address':24}: {self.fat2_address}\n"
               f"    {'base cluster address':24}: {self.base_cluster_address}\n"
               f">"
        )
    
    def _load_fats(self):
        """
        Reads the FATs from disk (hardcoded to 2 FATs, because there should
        only be two of them).
        """
        spf = self.sectors_per_fat
        bps = self.bytes_per_sector
        self._handle.seek(self.fat1_address)
        raw_fat = self._handle.read(spf * bps)
        self.fat1 = [ v[0] for v in struct.iter_unpack("<L", raw_fat) ]
        # since we're literally where the second FAT starts, we can just read
        # from here on
        raw_fat = self._handle.read(spf * bps)
        self.fat2 = [ v[0] for v in struct.iter_unpack("<L", raw_fat) ]
    
    def _cluster_address(self, cluster):
        """
        Calculates `cluster` address in the file the filesystem is being read
        from.

        :param cluster: cluster number to get the address of
        :return: offset in base file at which the cluster starts
        """
        cluster -= 2
        bps = self.bytes_per_sector
        spc = self.sectors_per_cluster
        bca = self.base_cluster_address
        return bca + (cluster * spc * bps)
    
    def _read_cluster(self, cluster, nclusters=1):
        """
        Reads `nclusters` (defaults to 1) from the filesystem, starting at
        position `cluster` (in clusters, the final address is converted 
        internally).

        :param cluster: cluster number to start reading from
        :param nclusters: amount of clusters to read (defaults to 1)
        :return: bytes read from the underlying file/device
        """
        bps = self.bytes_per_sector
        spc = self.sectors_per_cluster
        bca = self.base_cluster_address
        # the first actual cluster is #2 (there are no #0 and #1) so we have to
        # adjust the cluster number we're going to read
        cluster -= 2
        pos = bca + (cluster * spc * bps)
        length = nclusters * bps * spc
        self._handle.seek(pos)
        return self._handle.read(length)
    
    def _post_init(self):
        """
        Finishes setting up values in the filesystem. Everything that comes here
        assumes the basic functionality of the filesystem is already working
        and adds ease-of-use things.
        """
        root = Directory(self, None)
        v_id = root.files[0]
        if v_id.attributes["volume-id"]:
            root.path = (v_id.name + v_id.ext).decode("ascii")
        self.root = root
    
    def open(self, path):
        """
        Opens a file or directory found in the absolute path passed.

        :param path: absolute path to open.
        :returns: FileHandle or Directory object, depending on the path.
        """
        path  = path.upper()
        path  = path.encode("latin-1")  # TODO: make the encoding an attribute...
        path  = path.replace(b"\\", b"/")
        parts = path.split(b"/")[1:]
        # we ignore the first one, assuming it's the root -- remember, these
        # should be absolute paths!
        obj = self.root
        for part in parts:
            try:
                files = obj.files
            except AttributeError:
                raise FileNotFoundError(f"{obj.path} is not a Directory!")
            try:
                idx = next( idx
                            for idx, f in enumerate(files)
                            if f.fullname == part
                )
            except StopIteration:
                raise FileNotFoundError(f"No such file or directory {obj.path}\\{part}")
            # if we're here, we got a a directory
            record = obj.files[idx]
            if record.attributes["directory"]:
                obj = Directory(self, record, parent=obj)
            else:
                obj = FileHandle(self, record, parent=obj)
                # hopefully this happens just once, otherwise 
        # we could safely assume our object is just fine...
        return obj
