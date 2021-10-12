"""
This module implements functions and classes to handle NTFS filesystems.

For the moment it only implements the the $STANDARD_INFORMATION and $FILENAME
attribute structures, plus a few convenience classes to parse $I30 records.
"""
import struct
import datetime



def timestamp(tics):
    """
    Converts a MS Timestamp into a datetime object.

    :param timestamp: 64 bit MS timestap (string)
    :return: datetime.datetime object of the timestamp
    """
    # Ref: https://docs.microsoft.com/en-us/windows/win32/api/minwinbase/ns-minwinbase-filetime
    days = tics // 864_000_000_000
    rem = tics % 864_000_000_000
    hours = rem // 36_000_000_000
    rem -= hours * 36_000_000_000
    minutes = rem // 600_000_000
    rem -= minutes * 600_000_000
    seconds = rem // 10_000_000
    rem -= seconds * 10_000_000
    microseconds = rem // 10
    td = datetime.timedelta(days)  # this way its easier to handle leap years
    date = datetime.datetime(1601, 1, 1, hours, minutes, seconds, microseconds) + td
    return date


class StandardInformation:
    st = struct.Struct("<QQQQLLLLLLQQ")

    def __init__(self, data=bytes(722), *,
                 ctime=None, mtime=None, rtime=None, atime=None, permissions=None,
                 max_version=None, version_num=None, class_id=None,
                 owner_id=None, security_id=None, quota=None, usn=None,
        ):
        """
        Represents the $STANDARD_INFORMATION attributes used in NTFS.

        :param data: the raw bytes that define the on-disk structure
        :return: StandardInformation object
        """
        self._raw_data = data
        p_ctime, p_mtime, p_rtime, p_atime, p_perm, p_maxver, p_vernum, \
            p_classid, p_owner, p_secid, p_quota, p_usn = self.st.unpack(data[:72])

        self.ctime = ctime or timestamp(p_ctime)  # creation
        self.mtime = mtime or timestamp(p_mtime)  # last modify
        self.rtime = rtime or timestamp(p_rtime)  # last record change
        self.atime = atime or timestamp(p_atime)  # last access
        self.permissions = permissions or p_perm
        self.max_version = max_version or p_maxver
        self.version_num = version_num or p_vernum
        self.class_id = class_id or p_classid
        self.owner_id = owner_id or p_owner
        self.security_id = security_id or p_secid
        self.quota = quota or p_quota
        self.usn = usn or p_usn


class FileName:
    st = struct.Struct("<QQQQQQQLLBB")
    # in order, these are for:
    #   parent_dir, ctime, atime, mtime, rtime, size_alloc, size_real, flags,
    #   reparse, filename_len, filename_namespace

    def __init__(self, data=bytes(66), *, 
                 parent=None, ctime=None, mtime=None, rtime=None, atime=None,
                 size_alloc=None, size_real=None, flags=None, reparse=None,
                 namespace=None, filename=None,
        ):
        """
        Object to represent $FILENAME attributes used in NTFS.

        :param data: the raw bytes that define the on-disk structure
        :return: StandardInformation object
        """
        self._raw_data = data  # first we keep it
        filename_len = len(filename) if filename else None
        # and now we parse
        p_parent, p_ctime, p_mtime, p_rtime, p_atime, p_size_alloc, \
            p_size_real, p_flags, p_reparse, p_len, \
            p_namespace = self.st.unpack(data[0: 0x42])
        p_filename = data[0x42: 0x42 + p_len * 2].decode("utf-16le")

        self.parent = parent or p_parent
        self.ctime = ctime or timestamp(p_ctime)  # creation
        self.mtime = mtime or timestamp(p_mtime)  # last modify
        self.rtime = rtime or timestamp(p_rtime)  # last record change
        self.atime = atime or timestamp(p_atime)  # last access
        self.size_alloc = size_alloc or p_size_alloc
        self.size_real = size_real or p_size_real
        self.flags = flags or p_flags
        self.reparse = reparse or p_reparse
        self.len = filename_len or p_len  # and yes, __len__ will return this
        self.namespace = namespace
        self.filename = filename or p_filename

        # at this point we're pretty much sure we have a valid-ish $FN record
        # so we can clip a bit of data at the end of the _raw_data attribute
        self._raw_data = data[: 0x42 + p_len * 2]

    def __repr__(self):
        return f"< $FN '{self.filename}'>"

class IndexEntry:
    # TODO: this is actually the INDX entry format for directory indexes
    #       there are other formats for other kinds of indexes in NTFS
    #       we may need to implement those later
    st = struct.Struct("<QHHHH")
    def __init__(self, data=bytes(88)):
        """
        Represents an entry in an $I30 file.

        :param data: raw-bytes that define the structure.
        :return: IndexEntry object
        """
        self._raw_data = data
        p_mft_ref, p_size_idx, p_size_stream, p_flags, _pad = self.st.unpack(data[0: 16])
        self.mft_ref = p_mft_ref
        self.size_idx = p_size_idx
        self.size_stream = p_size_stream
        self.flags = p_flags
        # and now we can instantiate the $FN part
        self.filename = FileName(data[16:])
    
    def __repr__(self):
        return f"< IndexEntry for '{self.filename.filename}'>"


class I30:
    st_header = struct.Struct("<4sHHQQLLLB3sH")
    # and then comes a variable amount that we have to read from...

    def __init__(self, data=bytes(42)):
        """
        Represents a whole $I30 file, parsing the header and entries.

        :param data: raw-bytes of the $I30 file.
        :return: I30 object
        """
        self._raw_data = data
        magic_, p_useq_offset, p_sz_useq, p_logfile_seq, p_vcn, \
            p_idx_offset, p_sz_entries, p_sz_alloc, p_flags, pad, \
            p_useq = self.st_header.unpack(data[:42])
        # now let's save...
        self.magic = magic_  # not really necessary, but we may validate later on
        self.useq_offset = p_useq_offset  # we'll do the None or ... later on if we need it
        self.sz_useq= p_sz_useq
        self.logfile_seq = p_logfile_seq
        self.vcn = p_vcn
        self.idx_offset = p_idx_offset
        self.sz_entries = p_sz_entries
        self.sz_alloc = p_sz_alloc
        self.flags = p_flags
        # padding
        self.useq = p_useq
        # and now we parse the entries
        self.entries = []
        offset = 0x18 + self.idx_offset
        while offset + 66 < self.sz_entries + 0x18:
            entry = IndexEntry(data[offset:])
            self.entries.append(entry)
            offset += entry.size_idx
        # and we're done!
        
    def __repr__(self):
        return f"< I30 file >"
    
    def __str__(self):
        ret = [
            f"< I30 file with",
            f"    useq_array_offset: {self.useq_offset}",
            f"    sz_useq          : {self.sz_useq}",
            f"    logfile_seq      : {self.logfile_seq}",
            f"    v. cluster num.  : {self.vcn}",
            f"    idx_offset       : {self.idx_offset}",
            f"    sz_entries       : {self.sz_entries}",
            f"    sz_alloc         : {self.sz_alloc}",
            f"    flags            : {self.flags}",  # maybe pretty print them?
            f"    useq             : {self.useq}",
            f">",
        ]
        return "\n".join(ret)
