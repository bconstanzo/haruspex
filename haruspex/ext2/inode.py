# To check:
#  - I'm not sure whether to do certain parse on the 'setter' or the 'getter' (like the case of 'i_mode' or 'i_flags')
#    -> FOR NOW, LET THEY REMAIN AS THEY ARE CURRENTLY.
#  - check if the inode functions (defined at the end of the class) have to be implemented somewhere.
#  - there is a small "issue" with the timestamps of files, because when doing a test on a pendrive that I formatted in ext2,
#    when reading any date/time, I realized that it was recorded/written in UTC-3 (my time zone),
#    and then the 'datetime.fromtimestamp()' method, when converting it to our time zone (UTC-3), it subtracts 3 hours,
#    then date is inconsistent. If when manipulating files on ext2, the dates are always written in the PC's time zone,
#    I have to add a parameter to the '.fromtimestamp()' method, so that it does not convert the date.
#    But the point is that when showing the dates, we will not know what time zone they belong to,
#    unless we know exactly the time zone of the PC where those dates were written.
#    WHATEVER CRITERION WE CHOOSE, APPLY THE SAME TO THE 'superblock.py' DATES.

import datetime
import struct

# Types of files recognized by Ext2 (used in 'i_mode' field)
file_types = {
    0x0: 'u', # "Unknown"
    0x1: 'p', # "Named pipe / FIFO"
    0x2: 'c', # "Character device"
    0x4: 'd', # "Directory"
    0x6: 'b', # "Block device"
    0x8: '-', # "Regular file"
    0xA: 'l', # "Symbolic link"
    0xC: 's', # "Socket"
}

# Permissions a user has on a file (used in 'i_mode' field)
access_rights = {
    0: '-', # denied  (b: 000)
    1: 'x', # execute (b: 001)
    2: 'w', # write   (b: 010)
    4: 'r', # read    (b: 100)
}

N_FLAGS = 14 # in case in the future I parse more (max 32)

# Flags indicate how ext2 should behave when accessing data pointed to by an inode.
file_flags = {
    # 0x0000: "", # (I was thinking of using this if I parsed it only as a string, and not as a list)
    # ---
    0x0001: "secure deletion",
    0x0002: "record for undelete",
    0x0004: "compressed file",
    0x0008: "synchronous updates",
    0x0010: "immutable file",
    0x0020: "append only",
    0x0040: "do not dump/delete file",
    0x0080: "do not update .i_atime",
    # -- Reserved for compression usage --
    0x0100: "dirty (modified)",
    0x0200: "compressed blocks",
    0x0400: "access raw compressed data",
    0x0800: "compression error",
    # ---
    0x1000: "b-tree format directory, hash indexed directory", # both have the same bit
    0x2000: "AFS directory"
    # 0x4000: "journal file data" # reserved for ext3
}

class Inode:
    """
    Class representing an i-node of an ext2 filesystem.
    An inode is associated with a file (or directory), and contains metadata
    about it and pointers to its assigned data blocks (or directory blocks).

    An inode corresponds to a single file, therefore there is one inode
    for each file (or directory) in the filesystem.

    All inodes have the same size: at least 128 bytes (which is what I parse; the fundamental part of an inode).
      if revision of ext2 = 0 -> inode_size = 128 bytes (always)
      if revision of ext2 > 0 -> 128 bytes <= inode_size <= block_size, and is a perfect power of 2
    (the superblock is who knows the value of inode_size, block_size and the revision of ext2)
    """
    def __init__(self, data=bytes(128),
                 i_mode=None, i_uid=None, i_size=None, i_atime=None, i_ctime=None,
                 i_mtime=None, i_dtime=None, i_gid=None, i_links_count=None,
                 i_blocks=None, i_flags=None, osd1=None, i_block=None, i_generation=None,
                 i_file_acl=None, i_dir_acl=None, i_faddr=None, osd2=None
                 ):

        p_i_mode        = struct.unpack("<H", data[0:2])[0]
        p_i_uid         = struct.unpack("<H", data[2:4])[0]
        p_i_size        = struct.unpack("<I", data[4:8])[0]
        p_i_atime       = struct.unpack("<I", data[8:12])[0]
        p_i_ctime       = struct.unpack("<I", data[12:16])[0]
        p_i_mtime       = struct.unpack("<I", data[16:20])[0]
        p_i_dtime       = struct.unpack("<I", data[20:24])[0]
        p_i_gid         = struct.unpack("<H", data[24:26])[0]
        p_i_links_count = struct.unpack("<H", data[26:28])[0]
        p_i_blocks      = struct.unpack("<I", data[28:32])[0]
        p_i_flags       = struct.unpack("<I", data[32:36])[0]
        p_osd1          = struct.unpack("<I", data[36:40])[0]
        p_i_block       = struct.unpack("<IIIIIIIIIIIIIII", data[40:100])
        p_i_generation  = struct.unpack("<I", data[100:104])[0]
        p_i_file_acl    = struct.unpack("<I", data[104:108])[0]
        p_i_dir_acl     = struct.unpack("<I", data[108:112])[0]
        p_i_faddr       = struct.unpack("<I", data[112:116])[0]
        p_osd2          = struct.unpack("<III", data[116:128])

        self._raw_data = data

        self.i_mode        = i_mode        or p_i_mode
        self.i_uid         = i_uid         or p_i_uid
        self.i_size        = i_size        or p_i_size
        self.i_atime       = i_atime       or p_i_atime
        self.i_ctime       = i_ctime       or p_i_ctime
        self.i_mtime       = i_mtime       or p_i_mtime
        self.i_dtime       = i_dtime       or p_i_dtime
        self.i_gid         = i_gid         or p_i_gid
        self.i_links_count = i_links_count or p_i_links_count
        self.i_blocks      = i_blocks      or p_i_blocks
        self.i_flags       = i_flags       or p_i_flags
        self.osd1          = osd1          or p_osd1
        self.i_block       = i_block       or p_i_block
        self.i_generation  = i_generation  or p_i_generation
        self.i_file_acl    = i_file_acl    or p_i_file_acl
        self.i_dir_acl     = i_dir_acl     or p_i_dir_acl
        self.i_faddr       = i_faddr       or p_i_faddr
        self.osd2          = osd2          or p_osd2

        # 'i_': inode ; 'p_': parsed

    @property
    def raw_data(self):
        """
        Bytes to be parsed.
        (are the 128 bytes corresponding to the base structure of an inode)
        """
        return self._raw_data

    @raw_data.setter
    def raw_data(self, value):
        pass

    # ---

    @property
    def i_mode(self):
        """
        File type and access rights (16 bits)
        The top 4 bits for the type, and the bottom 12 bits for the access rights.

        Returns a formatted-string (based on how it actually shows on Linux)
        """
        f_type   = self._i_mode >> 12
        permissions = f"{file_types[f_type]}"

        f_rights = self._i_mode & 0x0fff

        # process control bits (I don't really concatenate them in the final string, for now)
        set_process_user_id =  ((f_rights & 0b100000000000) >> 11) == 1
        set_process_group_id = ((f_rights & 0b010000000000) >> 10) == 1
        sticky_bit =           ((f_rights & 0b001000000000) >>  9) == 1

        # access rights bits
        owner_rights = (f_rights & 0b000111000000) >> 6
        group_rights = (f_rights & 0b000000111000) >> 3
        other_rights = (f_rights & 0b000000000111)

        rights = [owner_rights, group_rights, other_rights]

        for r in rights:
            permissions += access_rights[r & 0b100] # each bit has a meaning
            permissions += access_rights[r & 0b010]
            permissions += access_rights[r & 0b001]

        # permissions += f"{set_process_user_id} {set_process_group_id} {sticky_bit}"

        return permissions

    @i_mode.setter
    def i_mode(self, value):
        self._i_mode = int(value)

    @property
    def i_uid(self):
        """
        Owner identifier
        """
        return self._i_uid

    @i_uid.setter
    def i_uid(self, value):
        self._i_uid = value

    @property
    def i_size(self):
        """
        Effective length of the file in bytes
        """
        return self._i_size

    @i_size.setter
    def i_size(self, value):
        self._i_size = int(value)

    # ---------------------------------------------------------

    # All 'timestamps' of files in ext2 are based on 'POSIX time' (https://en.wikipedia.org/wiki/Unix_time),
    # that is, the number of seconds that have elapsed since the Unix epoch
    # (january 1st 1970, 00:00:00 UTC). All the fields that store dates in ext2,
    # have 4 bytes (unsigned), therefore 2^32 seconds can be stored (it will be enough until the year 2106 :-) )
    # Python has a method of the class 'datetime' (datetime module) that converts
    # 'POSIX time' to local time (it converts it to our time zone, not to UTC 0, which comes in handy)
    # See: https://docs.python.org/3/library/datetime.html#datetime.datetime.fromtimestamp
    # So, I will represent the timestamps with DateTime objects.

    @property
    def i_atime(self):
        """
        Last access timestamp
        """
        # https://docs.python.org/3/library/datetime.html#datetime.datetime.timestamp
        ts = self._i_atime if self._i_atime.timestamp() > 0. else None # if seconds elapsed since Unix epoch > 0.
        return ts

    @i_atime.setter
    def i_atime(self, value):
        # value: seconds elapsed since Unix epoch
        #self._i_atime = datetime.datetime.fromtimestamp(value) # DateTime object
        self._i_atime = datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc)
        # last edit: for now I keep the date as it comes, I don't convert it to the current PC time zone.

        # > According to what I researched, the dates should be written to the filesystem in UTC+0,
        #   but on testing, they are written according to the computer's time zone, that is,
        #   instead of converting the PC's time zone to UTC+0 and then do the subtraction
        #   'system_datetime_utc0 - unix_epoch' to obtain the resulting seconds,
        #   the subtraction is directly done with the current date of the PC.

    @property
    def i_ctime(self):
        """
        Metadata last modification timestamp (inode)
        """
        ts = self._i_ctime if self._i_ctime.timestamp() > 0. else None
        return ts

    @i_ctime.setter
    def i_ctime(self, value):
        #self._i_ctime = datetime.datetime.fromtimestamp(value)
        self._i_ctime = datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc)

    @property
    def i_mtime(self):
        """
        Data last modification timestamp (file contents)
        """
        ts = self._i_mtime if self._i_mtime.timestamp() > 0. else None
        return ts

    @i_mtime.setter
    def i_mtime(self, value):
        #self._i_mtime = datetime.datetime.fromtimestamp(value)
        self._i_mtime = datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc)

    @property
    def i_dtime(self):
        """
        Deletion timestamp        
        """
        ts = self._i_dtime if self._i_dtime.timestamp() > 0. else None
        return ts

    @i_dtime.setter
    def i_dtime(self, value):
        #self._i_dtime = datetime.datetime.fromtimestamp(value)
        self._i_dtime = datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc)

    # ---------------------------------------------------------

    @property
    def i_gid(self):
        """
        Group identifier
        """
        return self._i_gid

    @i_gid.setter
    def i_gid(self, value):
        self._i_gid = value

    @property
    def i_links_count(self):
        """
        Hard links counter
        """
        return self._i_links_count

    @i_links_count.setter
    def i_links_count(self, value):
        self._i_links_count = int(value)

    @property
    def i_blocks(self):
        """
        Number of data blocks (in units of 512 bytes) that have been allocated
        to the file (count of disk sectors).
        """
        return self._i_blocks

    @i_blocks.setter
    def i_blocks(self, value):
        self._i_blocks = int(value)

    @property
    def i_flags(self):
        """
        Returns a formated-string with the flags of the file
        """
        flag_list = []
        for b in range(0, N_FLAGS):         # I parse (for now) only 'n' bits of the 32 that "_i_flags" has.
            k = self._i_flags & (0b1 << b)  # I am applying masks of the type 1, 10, 100, 1000 ... (bits).
            if k != 0:
                flag_list.append(file_flags[k]) # the bits 0s will represent an empty string, and the 1s, a flag.
        return ", ".join(flag_list) # I do this to make the string look "better".
        # I'm not sure if this could be done with a "List Comprehension".

    @i_flags.setter
    def i_flags(self, value):
        self._i_flags = int(value)

    @property
    def osd1(self):
        """
        Specific operating system information (4 bytes)
        """
        return self._osd1

    @osd1.setter
    def osd1(self, value):
        self._osd1 = value

    @property
    def i_block(self):
        """
        Pointers to data blocks (12 direct and 3 indirect). I will store them in a list.
        Pointers to 0 are equal to null pointers, which means there is no block assigned/allocated yet.
        Otherwise, the value stored in the pointer is the block number that it refers to.
        """
        return self._i_block

    @i_block.setter
    def i_block(self, value):
        self._i_block = list(value)

    @property
    def i_generation(self):
        """
        File version (used when the file is accessed by a network filesystem)
        """
        return self._i_generation

    @i_generation.setter
    def i_generation(self, value):
        self._i_generation = value

    @property
    def i_file_acl(self):
        """
        File access control list
        """
        return self._i_file_acl

    @i_file_acl.setter
    def i_file_acl(self, value):
        self._i_file_acl = value

    @property
    def i_dir_acl(self):
        """
        Directory access control list (is not used for regular files)
        """
        return self._i_dir_acl

    @i_dir_acl.setter
    def i_dir_acl(self, value):
        self._i_dir_acl = value

    @property
    def i_faddr(self):
        """
        Fragment address
        """
        return self._i_faddr

    @i_faddr.setter
    def i_faddr(self, value):
        self._i_faddr = value

    @property
    def osd2(self):
        """
        Specific operating system information (12 bytes)
        """
        return self._osd2

    @osd2.setter
    def osd2(self, value):
        self._osd2 = value

    def __str__(self):
        return (
                f"File type and access rights:          {self.i_mode}\n"
                f"Owner identifier:                     {self.i_uid}\n"
                f"File length in bytes:                 {self.i_size}\n"
                f"Time of last file access:             {self.i_atime or 'Not defined'}\n"
                f"Time that inode last changed:         {self.i_ctime or 'Not defined'}\n"
                f"Time that file contents last changed: {self.i_mtime or 'Not defined'}\n"
                f"Time of file deletion:                {self.i_dtime or 'Not defined'}\n"
                f"Group identifier:                     {self.i_gid}\n"
                f"Hard links counter:                   {self.i_links_count}\n"
                f"Number of data blocks of the file:    {self.i_blocks} (in units of 512 bytes)\n"
                f"File flags:                           {self.i_flags}\n"
                f"Direct pointers to data blocks:       {self.i_block[0:12]}\n"
                f"Pointer to simple indirect block:     {self.i_block[12]}\n"
                f"Pointer to doubly-indirect block:     {self.i_block[13]}\n"
                f"Pointer to triply-indirect block:     {self.i_block[14]}\n"
                # some fields would be missing (which for the moment I decided not to show them).
            )

    # Ext2 Inode Operations

    # only if the inode refers to a regular file
    def ext2_truncate():
        pass

    # only if the inode refers to a directory
    def ext2_create():
        pass

    def ext2_lookup():
        pass

    def ext2_link():
        pass

    def ext2_unlink():
        pass

    def ext2_symlink():
        pass

    def ext2_mkdir():
        pass

    def ext2_rmdir():
        pass

    def ext2_mknod():
        pass

    def ext2_rename():
        pass

    # only if the inode refers to a symbolic link that can be fully stored inside the inode itself
    def ext2_readlink():
        pass

    def ext2_follow_link():
        pass

    # Note: If the inode refers to a character device file, to a block device file,
    #       or to a named pipe, the inode operations do not depend on the filesystem.

