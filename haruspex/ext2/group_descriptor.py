# To check:
#  - decide whether or not to show the attributes 'bg_pad' and 'bg_reserved' in '__str__'.
#  - In an 'ext2/3' book, this section of the group descriptor also talks about
#    data block and inode bitmaps, but I think I'll touch on that when I make
#    the 'ext2' class that handles everything. EDIT: it was not necessary to parse them.

import struct

class GroupDescriptor:
    """
    Class representing a Group Descriptor of an ext2 filesystem.
    Each block group has its own group descriptor (which has information about the group).

    Actually, each block group contains a table of group descriptors,
    that is, each entry contains the information of each block group in the filesystem.
    (yes, just like the superblock, there is a copy of this table in each block group)
    """
    def __init__(self, data=bytes(32),
                 bg_block_bitmap=None, bg_inode_bitmap=None, bg_inode_table=None,
                 bg_free_blocks_count=None, bg_free_inodes_count=None,
                 bg_used_dirs_count=None, bg_pad=None, bg_reserved=None
                 ):
        
        p_bg_block_bitmap      = struct.unpack("<I", data[0:4])[0]
        p_bg_inode_bitmap      = struct.unpack("<I", data[4:8])[0]
        p_bg_inode_table       = struct.unpack("<I", data[8:12])[0]
        p_bg_free_blocks_count = struct.unpack("<H", data[12:14])[0]
        p_bg_free_inodes_count = struct.unpack("<H", data[14:16])[0]
        p_bg_used_dirs_count   = struct.unpack("<H", data[16:18])[0]
        p_bg_pad               = struct.unpack("<H", data[18:20])[0]
        p_bg_reserved          = struct.unpack("<III", data[20:32])

        self._raw_data = data

        self.bg_block_bitmap      = bg_block_bitmap      or p_bg_block_bitmap
        self.bg_inode_bitmap      = bg_inode_bitmap      or p_bg_inode_bitmap
        self.bg_inode_table       = bg_inode_table       or p_bg_inode_table
        self.bg_free_blocks_count = bg_free_blocks_count or p_bg_free_blocks_count
        self.bg_free_inodes_count = bg_free_inodes_count or p_bg_free_inodes_count
        self.bg_used_dirs_count   = bg_used_dirs_count   or p_bg_used_dirs_count
        self.bg_pad               = bg_pad               or p_bg_pad
        self.bg_reserved          = bg_reserved          or p_bg_reserved

        # 'bg_': block group ; 'p_': parsed

    @property
    def raw_data(self):
        """
        Bytes to be parsed.
        (are the 32 bytes corresponding to the structure of a group descriptor)
        """
        return self._raw_data

    @raw_data.setter
    def raw_data(self, value):
        pass

    # ---

    @property
    def bg_block_bitmap(self):
        """
        Block number of block bitmap.
        """
        return self._bg_block_bitmap

    @bg_block_bitmap.setter
    def bg_block_bitmap(self, value):
        self._bg_block_bitmap = int(value)

    @property
    def bg_inode_bitmap(self):
        """
        Block number of inode bitmap.
        """
        return self._bg_inode_bitmap

    @bg_inode_bitmap.setter
    def bg_inode_bitmap(self, value):
        self._bg_inode_bitmap = int(value)

    @property
    def bg_inode_table(self):
        """
        Block number of first inode table block.
        """
        return self._bg_inode_table

    @bg_inode_table.setter
    def bg_inode_table(self, value):
        self._bg_inode_table = int(value)

    @property
    def bg_free_blocks_count(self):
        """
        Number of free blocks in the group.
        """
        return self._bg_free_blocks_count

    @bg_free_blocks_count.setter
    def bg_free_blocks_count(self, value):
        self._bg_free_blocks_count = int(value)

    @property
    def bg_free_inodes_count(self):
        """
        Number of free inodes in the group.
        """
        return self._bg_free_inodes_count

    @bg_free_inodes_count.setter
    def bg_free_inodes_count(self, value):
        self._bg_free_inodes_count = int(value)

    @property
    def bg_used_dirs_count(self):
        """
        Number of directories in the group.
        """
        return self._bg_used_dirs_count

    @bg_used_dirs_count.setter
    def bg_used_dirs_count(self, value):
        self._bg_used_dirs_count = int(value)

    @property
    def bg_pad(self):
        """
        16bit value used for padding the structure on a 32bit boundary.
        (Alignment to word)
        """
        return self._bg_pad

    @bg_pad.setter
    def bg_pad(self, value):
        self._bg_pad = value

    @property
    def bg_reserved(self):
        """
        12 bytes of reserved space for future revisions.
        (Nulls to pad out 32 bytes)
        """
        return self._bg_reserved

    @bg_reserved.setter
    def bg_reserved(self, value):
        self._bg_reserved = value

    # ---

    def __str__(self):
        return (
                f"Block number of block bitmap:            {self.bg_block_bitmap}\n"
                f"Block number of inode bitmap:            {self.bg_inode_bitmap}\n"
                f"Block number of first inode table block: {self.bg_inode_table}\n"
                f"Number of free blocks in the group:      {self.bg_free_blocks_count}\n"
                f"Number of free inodes in the group:      {self.bg_free_inodes_count}\n"
                f"Number of directories in the group:      {self.bg_used_dirs_count}\n"
                f"Alignment to word:                       {self.bg_pad}\n"
                f"Nulls to pad out 32 bytes:               {self.bg_reserved}\n"
            )

