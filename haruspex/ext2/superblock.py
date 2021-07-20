# To check:
#  - decide if the 'getter' thing should go in the 'setter' (in s_log_block_size and s_state).
#    -> FOR NOW LET EVERYTHING STAY AS IT IS NOW
#  - check if the superblock's own methods/operations (defined last) should be implemented somewhere.
#  - what I commented in 's_uuid.setter'.
#  - maybe it would be necessary to implement the getter of 's_feature_compat',
#    's_feature_incompat' and 's_feature_ro_compat' (https://www.nongnu.org/ext2-doc/ext2.html#s-feature-compat).
#  - maybe it would be necessary to implement the getter of 's_algo_bitmap' (https://www.nongnu.org/ext2-doc/ext2.html#s-algo-bitmap).
#  - maybe it would be nice to add the '__len __()' dunder method, which shows the size of the structure (and also in the other classes).

import datetime
import struct

# Volume name and Pathname of last mount point encoding
ENCODING = 'latin-1' # generally latin-1 is used

class Superblock:
    """
    Class representing the Superblock of an ext2 filesystem.
    The superblock contains all the information about the configuration of the filesystem.
    (there is a copy of the superblock in each block group in the filesystem)

    The superblock is always starting at the 1024th byte of the disk's partition,
    which normally happens to be the first byte of the 3rd sector (assuming 512-byte sectors).
    """
    def __init__(self, data=bytes(1024),
                 s_inodes_count=None, s_blocks_count=None, s_r_blocks_count=None,
                 s_free_blocks_count=None, s_free_inodes_count=None, s_first_data_block=None,
                 s_log_block_size=None, s_log_frag_size=None, s_blocks_per_group=None,
                 s_frags_per_group=None, s_inodes_per_group=None, s_mtime=None,
                 s_wtime=None, s_mnt_count=None, s_max_mnt_count=None, s_magic=None,
                 s_state=None, s_errors=None, s_minor_rev_level=None, s_lastcheck=None,
                 s_checkinterval=None, s_creator_os=None, s_rev_level=None,
                 s_def_resuid=None, s_def_resgid=None, s_first_ino=None, s_inode_size=None,
                 s_block_group_nr=None, s_feature_compat=None, s_feature_incompat=None,
                 s_feature_ro_compat=None, s_uuid=None, s_volume_name=None,
                 s_last_mounted=None, s_algorithm_usage_bitmap=None, s_prealloc_blocks=None,
                 s_prealloc_dir_blocks=None, s_padding1=None, s_reserved=None
                 ):
        
        # All fields in the superblock (as in all other ext2 structures) are stored
        # on the disk in little endian format (<)

        # 'I' represents a 32-bit unsigned int format
        # 'i' represents a 32-bit signed int format
        # See more in: https://docs.python.org/3/library/struct.html

        p_s_inodes_count      = struct.unpack("<I", data[0:4])[0]
        p_s_blocks_count      = struct.unpack("<I", data[4:8])[0]
        p_s_r_blocks_count    = struct.unpack("<I", data[8:12])[0]
        p_s_free_blocks_count = struct.unpack("<I", data[12:16])[0]
        p_s_free_inodes_count = struct.unpack("<I", data[16:20])[0]
        p_s_first_data_block  = struct.unpack("<I", data[20:24])[0]
        p_s_log_block_size    = struct.unpack("<I", data[24:28])[0]
        p_s_log_frag_size     = struct.unpack("<i", data[28:32])[0]
        p_s_blocks_per_group  = struct.unpack("<I", data[32:36])[0]
        p_s_frags_per_group   = struct.unpack("<I", data[36:40])[0]
        p_s_inodes_per_group  = struct.unpack("<I", data[40:44])[0]
        #
        p_s_mtime             = struct.unpack("<I", data[44:48])[0]
        p_s_wtime             = struct.unpack("<I", data[48:52])[0]
        p_s_mnt_count         = struct.unpack("<H", data[52:54])[0]
        p_s_max_mnt_count     = struct.unpack("<H", data[54:56])[0]
        p_s_magic             = struct.unpack("<H", data[56:58])[0]
        p_s_state             = struct.unpack("<H", data[58:60])[0]
        p_s_errors            = struct.unpack("<H", data[60:62])[0]
        p_s_minor_rev_level   = struct.unpack("<H", data[62:64])[0]
        p_s_lastcheck         = struct.unpack("<I", data[64:68])[0]
        p_s_checkinterval     = struct.unpack("<I", data[68:72])[0]
        p_s_creator_os        = struct.unpack("<I", data[72:76])[0]
        p_s_rev_level         = struct.unpack("<I", data[76:80])[0]
        p_s_def_resuid        = struct.unpack("<H", data[80:82])[0]
        p_s_def_resgid        = struct.unpack("<H", data[82:84])[0]
        #
        p_s_first_ino         = struct.unpack("<I", data[84:88])[0]
        p_s_inode_size        = struct.unpack("<H", data[88:90])[0]
        p_s_block_group_nr    = struct.unpack("<H", data[90:92])[0]
        #
        p_s_feature_compat    = struct.unpack("<I", data[92:96])[0]
        p_s_feature_incompat  = struct.unpack("<I", data[96:100])[0]
        p_s_feature_ro_compat = struct.unpack("<I", data[100:104])[0]
        p_s_uuid              = struct.unpack("<BBBBBBBBBBBBBBBB", data[104:120])
        p_s_volume_name       = data[120:136] # Volume name
        p_s_last_mounted      = data[136:200] # Pathname of last mount point
        p_s_algorithm_usage_bitmap = struct.unpack("<I", data[200:204])[0]
        p_s_prealloc_blocks        = struct.unpack("<B", data[204:205])[0]
        p_s_prealloc_dir_blocks    = struct.unpack("<B", data[205:206])[0]
        #
        p_s_padding1          = struct.unpack("<H", data[206:208])[0]
        p_s_reserved          = data[208:1024]
        # for ext3 there are some more fields: https://www.nongnu.org/ext2-doc/ext2.html#superblock

        self._raw_data = data # the raw read from the disk (the 1024 bytes of the superblock).

        self.s_inodes_count      = s_inodes_count      or p_s_inodes_count
        self.s_blocks_count      = s_blocks_count      or p_s_blocks_count
        self.s_r_blocks_count    = s_r_blocks_count    or p_s_r_blocks_count
        self.s_free_blocks_count = s_free_blocks_count or p_s_free_blocks_count
        self.s_free_inodes_count = s_free_inodes_count or p_s_free_inodes_count
        self.s_first_data_block  = s_first_data_block  or p_s_first_data_block
        self.s_log_block_size    = s_log_block_size    or p_s_log_block_size
        self.s_log_frag_size     = s_log_frag_size     or p_s_log_frag_size
        self.s_blocks_per_group  = s_blocks_per_group  or p_s_blocks_per_group
        self.s_frags_per_group   = s_frags_per_group   or p_s_frags_per_group
        self.s_inodes_per_group  = s_inodes_per_group  or p_s_inodes_per_group
        #
        self.s_mtime             = s_mtime             or p_s_mtime
        self.s_wtime             = s_wtime             or p_s_wtime
        self.s_mnt_count         = s_mnt_count         or p_s_mnt_count
        self.s_max_mnt_count     = s_max_mnt_count     or p_s_max_mnt_count
        self.s_magic             = s_magic             or p_s_magic
        self.s_state             = s_state             or p_s_state
        self.s_errors            = s_errors            or p_s_errors
        self.s_minor_rev_level   = s_minor_rev_level   or p_s_minor_rev_level
        self.s_lastcheck         = s_lastcheck         or p_s_lastcheck
        self.s_checkinterval     = s_checkinterval     or p_s_checkinterval
        self.s_creator_os        = s_creator_os        or p_s_creator_os
        self.s_rev_level         = s_rev_level         or p_s_rev_level
        self.s_def_resuid        = s_def_resuid        or p_s_def_resuid
        self.s_def_resgid        = s_def_resgid        or p_s_def_resgid
        #
        self.s_first_ino         = s_first_ino         or p_s_first_ino
        self.s_inode_size        = s_inode_size        or p_s_inode_size
        self.s_block_group_nr    = s_block_group_nr    or p_s_block_group_nr
        #
        self.s_feature_compat         = s_feature_compat         or p_s_feature_compat
        self.s_feature_incompat       = s_feature_incompat       or p_s_feature_incompat
        self.s_feature_ro_compat      = s_feature_ro_compat      or p_s_feature_ro_compat
        self.s_uuid                   = s_uuid                   or p_s_uuid
        self.s_volume_name            = s_volume_name            or p_s_volume_name
        self.s_last_mounted           = s_last_mounted           or p_s_last_mounted
        self.s_algorithm_usage_bitmap = s_algorithm_usage_bitmap or p_s_algorithm_usage_bitmap
        self.s_prealloc_blocks        = s_prealloc_blocks        or p_s_prealloc_blocks
        self.s_prealloc_dir_blocks    = s_prealloc_dir_blocks    or p_s_prealloc_dir_blocks
        #
        self.s_padding1 = s_padding1 or p_s_padding1
        self.s_reserved = s_reserved or p_s_reserved

        # 's_': superblock ; 'p_': parsed

    @property
    def raw_data(self):
        """
        Bytes to be parsed.
        (are the 1024 bytes corresponding to the structure of the superblock)
        """
        return self._raw_data

    @raw_data.setter
    def raw_data(self, value):
        pass

    # ---

    @property
    def s_inodes_count(self):
        """Total number of inodes"""
        return self._s_inodes_count

    @s_inodes_count.setter
    def s_inodes_count(self, value):
        self._s_inodes_count = int(value)

    @property
    def s_blocks_count(self):
        """Filesystem size in blocks"""
        return self._s_blocks_count

    @s_blocks_count.setter
    def s_blocks_count(self, value):
        self._s_blocks_count = int(value)

    @property
    def s_r_blocks_count(self):
        """Number of reserved blocks"""
        return self._s_r_blocks_count

    @s_r_blocks_count.setter
    def s_r_blocks_count(self, value):
        self._s_r_blocks_count = int(value)

    @property
    def s_free_blocks_count(self):
        """
        Free blocks counter
        (data blocks + directory-entry blocks)
        """
        return self._s_free_blocks_count

    @s_free_blocks_count.setter
    def s_free_blocks_count(self, value):
        self._s_free_blocks_count = int(value)

    @property
    def s_free_inodes_count(self):
        """
        Free inodes counter
        The inodes are each of the entries in the inode table, and this table
        has a calculable size. Creating an inode does not mean that a new block
        is allocated from the file system, but rather to fill in a new entry in the table.
        Therefore, "s_free_inodes_count" is an independent calculation of "s_free_blocks_count".
        """
        return self._s_free_inodes_count

    @s_free_inodes_count.setter
    def s_free_inodes_count(self, value):
        self._s_free_inodes_count = int(value)

    @property
    def s_first_data_block(self):
        """
        Number of first useful block.
        It is the id of the block containing the superblock structure.

        This value is always 0 for filesystems with a block size larger than 1KB,
        and always 1 for filesystems with a block size of 1KB, since the superblock
        is always starting at the 1024th byte of the disk's partition.
        """
        return self._s_first_data_block

    @s_first_data_block.setter
    def s_first_data_block(self, value):
        self._s_first_data_block = int(value)

    @property
    def s_log_block_size(self):
        """
        The s_log_block_size field expresses the block size as a power of 2,
        using 1,024 bytes as the unit. Thus, 0 denotes 1,024-byte blocks,
        1 denotes 2,048-byte blocks, and so on.
        """
        size = 2**(10+self._s_log_block_size)
        return size
        
        # I think this would be fine, that is, if from 'outside' someone
        # wants to see the size of the block, they will directly see the size in bytes.
        # And that the true value of the attribute (0, 1 or 2), can only be accessed internally
        # (from here, the source code, doing self._s_log_block_size).

    @s_log_block_size.setter
    def s_log_block_size(self, value):
        # Valid block size values are 1024, 2048 and 4096 bytes.
        # (actually, in Linux the block size is limited by the architecture page size)
        if value > 2:
            value = 2
        self._s_log_block_size = value

    @property
    def s_log_frag_size(self):
        """
        Fragment size (not implemented in ext2)
        The s_log_frag_size field is currently equal to s_log_block_size,
        since block fragmentation is not yet implemented.
        """
        if(self._s_log_frag_size >= 0):
            # this is equivalent to what was done in "s_log_block_size"
            fragment_size = 1024 << self._s_log_frag_size;
        else:
            fragment_size = 1024 >> -self._s_log_frag_size;
        return fragment_size

    @s_log_frag_size.setter
    def s_log_frag_size(self, value):
        # The type of the s_log_frag_size field is signed integer,
        # unlike s_log_block_size which is unsigned integer.
        if value > 2:
            value = 2
        elif value < -2:
            value = -2
        self._s_log_frag_size = value

    @property
    def s_blocks_per_group(self):
        """Number of blocks per group"""
        return self._s_blocks_per_group

    @s_blocks_per_group.setter
    def s_blocks_per_group(self, value):
        self._s_blocks_per_group = int(value)

    @property
    def s_frags_per_group(self):
        """Number of fragments per group"""
        return self._s_frags_per_group

    @s_frags_per_group.setter
    def s_frags_per_group(self, value):
        self._s_frags_per_group = int(value)

    @property
    def s_inodes_per_group(self):
        """Number of inodes per group"""
        return self._s_inodes_per_group

    @s_inodes_per_group.setter
    def s_inodes_per_group(self, value):
        self._s_inodes_per_group = int(value)

    # ---

    @property
    def s_mtime(self):
        """Time of last mount operation [POSIX time]"""
        ts = self._s_mtime if self._s_mtime.timestamp() > 0. else "Not defined"
        return ts

    @s_mtime.setter
    def s_mtime(self, value):
        # I will use DateTime objects for timestamps (this is explained in 'inode.py')
        self._s_mtime = datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc)

    @property
    def s_wtime(self):
        """Time of last write operation [POSIX time]"""
        ts = self._s_wtime if self._s_wtime.timestamp() > 0. else "Not defined"
        return ts

    @s_wtime.setter
    def s_wtime(self, value):
        self._s_wtime = datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc)

    @property
    def s_mnt_count(self):
        """Mount operations counter"""
        return self._s_mnt_count

    @s_mnt_count.setter
    def s_mnt_count(self, value):
        self._s_mnt_count = int(value)

    @property
    def s_max_mnt_count(self):
        """Number of mount operations before check"""
        return self._s_max_mnt_count

    @s_max_mnt_count.setter
    def s_max_mnt_count(self, value):
        self._s_max_mnt_count = int(value)

    @property
    def s_magic(self):
        """
        Magic signature (fixed to 0xEF53)
        16bit value identifying the file system as Ext2.
        """
        return hex(self._s_magic)

    @s_magic.setter
    def s_magic(self, value):
        self._s_magic = int(value)
    
    @property
    def s_state(self):
        """
        Status flag: the s_state field stores the value 0 if the filesystem
        is mounted or was not cleanly unmounted, 1 if it was cleanly unmounted,
        and 2 if it contains errors.

        I return a string representing the status.
        """
        status = "unknown"

        if self._s_state == 0:
            status = "the filesystem is mounted or was not cleanly unmounted"
        elif self._s_state == 1:
            status = "the filesystem was cleanly unmounted"
        elif self._s_state == 2:
            status = "the filesystem contains errors"

        return status

    @s_state.setter
    def s_state(self, value):
        self._s_state = int(value)

    @property
    def s_errors(self):
        """Behavior of the filesystem driver when detecting errors"""
        behavior = "undefined"

        if self._s_errors == 1:
            behavior = "continue as if nothing happened"
        elif self._s_errors == 2:
            behavior = "remount read-only"
        elif self._s_errors == 3:
            behavior = "cause a kernel panic"

        return behavior

    @s_errors.setter
    def s_errors(self, value):
        self._s_errors = int(value)

    @property
    def s_minor_rev_level(self):
        """Minor revision level"""
        return self._s_minor_rev_level

    @s_minor_rev_level.setter
    def s_minor_rev_level(self, value):
        self._s_minor_rev_level = int(value)

    @property
    def s_lastcheck(self):
        """Time of last check [POSIX time]"""
        ts = self._s_lastcheck if self._s_lastcheck.timestamp() > 0. else "Not defined"
        return ts
    
    @s_lastcheck.setter
    def s_lastcheck(self, value):
        self._s_lastcheck = datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc)

    @property
    def s_checkinterval(self):
        """Time between checks [POSIX time]"""
        # https://docs.python.org/3/library/datetime.html#datetime.timedelta.total_seconds
        interval = self._s_checkinterval if self._s_checkinterval.total_seconds() > 0. else "Not defined"
        return interval

    @s_checkinterval.setter
    def s_checkinterval(self, value):
        # https://docs.python.org/3/library/datetime.html#timedelta-objects
        self._s_checkinterval = datetime.timedelta(seconds=value) # a 'timedelta' object represents a duration

    @property
    def s_creator_os(self):
        """OS where filesystem was created"""
        os = "unknown"

        if self._s_creator_os == 0:
            os = "Linux"
        elif self._s_creator_os == 1:
            os = "GNU HURD"
        elif self._s_creator_os == 2:
            os = "MASIX"
        elif self._s_creator_os == 3:
            os = "FreeBSD"
        elif self._s_creator_os == 4:
            os = "Lites"

        return os

    @s_creator_os.setter
    def s_creator_os(self, value):
        self._s_creator_os = int(value)

    @property
    def s_rev_level(self):
        """Revision level (0: revision 0 ; 1: revision 1)"""
        return self._s_rev_level

    @s_rev_level.setter
    def s_rev_level(self, value):
        self._s_rev_level = int(value)

    @property
    def s_def_resuid(self):
        """Default User ID for reserved blocks (in Linux it is 0)"""
        return self._s_def_resuid

    @s_def_resuid.setter
    def s_def_resuid(self, value):
        self._s_def_resuid = int(value)

    @property
    def s_def_resgid(self):
        """Default Group ID for reserved blocks (in Linux it is 0)"""
        return self._s_def_resgid

    @s_def_resgid.setter
    def s_def_resgid(self, value):
        self._s_def_resgid = int(value)

    # ---

    @property
    def s_first_ino(self):
        """
        Number of first nonreserved inode

        In revision 0, the first non-reserved inode is fixed to 11.
        In revision 1 and later this value may be set to any value.
        """
        return self._s_first_ino

    @s_first_ino.setter
    def s_first_ino(self, value):
        self._s_first_ino = int(value)

    @property
    def s_inode_size(self):
        """
        Size of on-disk inode structure

        In revision 0, this value is always 128.
        In revision 1 and later, this value must be a perfect power of 2
        and must be smaller or equal to the block size.
        """
        return self._s_inode_size

    @s_inode_size.setter
    def s_inode_size(self, value):
        self._s_inode_size = int(value)

    @property
    def s_block_group_nr(self):
        """Block group number of this superblock (this can be used to rebuild
        the file system from any superblock backup)"""
        return self._s_block_group_nr

    @s_block_group_nr.setter
    def s_block_group_nr(self, value):
        self._s_block_group_nr = int(value)

    # ---
    
    @property
    def s_feature_compat(self):
        """Compatible features bitmap"""
        return self._s_feature_compat

    @s_feature_compat.setter
    def s_feature_compat(self, value):
        self._s_feature_compat = value

    @property
    def s_feature_incompat(self):
        """Incompatible features bitmap"""
        return self._s_feature_incompat

    @s_feature_incompat.setter
    def s_feature_incompat(self, value):
        self._s_feature_incompat = value

    @property
    def s_feature_ro_compat(self):
        """Read-only compatible features bitmap"""
        return self._s_feature_ro_compat

    @s_feature_ro_compat.setter
    def s_feature_ro_compat(self, value):
        self._s_feature_ro_compat = value

    @property
    def s_uuid(self):
        """128-bit filesystem identifier"""
        f_id = str(self._s_uuid).replace(", ", "-")
        return f_id

    @s_uuid.setter
    def s_uuid(self, value):
        # I'm not sure if the ID is divided into 16 bytes, or is it directly a 16-byte number.
        self._s_uuid = tuple(value)

    @property
    def s_volume_name(self):
        """Volume name"""
        return self._s_volume_name

    @s_volume_name.setter
    def s_volume_name(self, value):
        # I admit both strings and bytestrings, but internally I keep bytestrings.
        if isinstance(value, str):
            value = bytes(value, ENCODING)
        self._s_volume_name = value.rstrip(b'\x00') # to remove trailing null chars

    @property
    def s_last_mounted(self):
        """Pathname of last mount point"""
        return self._s_last_mounted

    @s_last_mounted.setter
    def s_last_mounted(self, value):
        # I admit both strings and bytestrings, but internally I keep bytestrings.
        if isinstance(value, str):
            value = bytes(value, ENCODING)
        self._s_last_mounted = value.rstrip(b'\x00') # to remove trailing null chars

    @property
    def s_algorithm_usage_bitmap(self):
        """Used for compression"""
        return self._s_algorithm_usage_bitmap

    @s_algorithm_usage_bitmap.setter
    def s_algorithm_usage_bitmap(self, value):
        self._s_algorithm_usage_bitmap = value

    @property
    def s_prealloc_blocks(self):
        """Number of blocks to preallocate for regular files"""
        return self._s_prealloc_blocks

    @s_prealloc_blocks.setter
    def s_prealloc_blocks(self, value):
        self._s_prealloc_blocks = int(value)

    @property
    def s_prealloc_dir_blocks(self):
        """Number of blocks to preallocate for directories"""
        return self._s_prealloc_dir_blocks

    @s_prealloc_dir_blocks.setter
    def s_prealloc_dir_blocks(self, value):
        self._s_prealloc_dir_blocks = int(value)

    # ---

    @property
    def s_padding1(self):
        """Alignment to word [2 bytes]"""
        return self._s_padding1

    @s_padding1.setter
    def s_padding1(self, value):
        self._s_padding1 = value

    @property
    def s_reserved(self):
        """Nulls to pad out 1,024 bytes [816 bytes]"""
        return self._s_reserved

    @s_reserved.setter
    def s_reserved(self, value):
        self._s_reserved = value


    # I do not show all the fields, only the ones that I found most interesting.
    def __str__(self):
        return (
                f"Total number of inodes:                          {self.s_inodes_count}\n"
                f"Filesystem size in blocks:                       {self.s_blocks_count}\n"
                f"Number of reserved blocks:                       {self.s_r_blocks_count}\n"
                f"Free blocks counter:                             {self.s_free_blocks_count}\n"
                f"Free inodes counter:                             {self.s_free_inodes_count}\n"
                f"Number of first useful block:                    {self.s_first_data_block}\n"
                f"Block size:                                      {self.s_log_block_size}\n"
                f"Fragment size:                                   {self.s_log_frag_size}\n"
                f"Number of blocks per group:                      {self.s_blocks_per_group}\n"
                f"Number of fragments per group:                   {self.s_frags_per_group}\n"
                f"Number of inodes per group:                      {self.s_inodes_per_group}\n"
                f"Time of last mount operation:                    {self.s_mtime}\n"
                f"Time of last write operation:                    {self.s_wtime}\n"
                f"Mount operations counter:                        {self.s_mnt_count}\n"
                f"Magic signature:                                 {self.s_magic}\n"
                f"Status flag:                                     {self.s_state}\n"
                f"Time of last check:                              {self.s_lastcheck}\n"
                f"Time between checks:                             {self.s_checkinterval}\n"
                f"OS where filesystem was created:                 {self.s_creator_os}\n"
                f"Revision level:                                  {self.s_rev_level}\n"
                f"Number of first nonreserved inode:               {self.s_first_ino}\n"
                f"Size of on-disk inode structure:                 {self.s_inode_size}\n"
                f"Block group number of this superblock:           {self.s_block_group_nr}\n"
                f"Filesystem identifier:                           {self.s_uuid}\n"
                f"Volume name:                                     {self.s_volume_name.decode(ENCODING)}\n"
                f"Pathname of last mount point:                    {self.s_last_mounted.decode(ENCODING)}\n"
                f"Number of blocks to preallocate:                 {self.s_prealloc_blocks}\n"
                f"Number of blocks to preallocate for directories: {self.s_prealloc_dir_blocks}\n"
            )

    
    # Ext2 Superblock Operations

    def read_inode():
        pass

    def write_inode():
        pass

    def put_inode():
        pass

    def delete_inode():
        pass

    def put_super():
        pass

    def write_super():
        pass

    def statfs():
        pass

    def remount_fs():
        pass
    
