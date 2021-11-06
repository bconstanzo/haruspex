"""
This module handles reading from an Ext2 filesystem.
"""

# For the future: implement the writing capability, and the parser of the ext3's journal.

# To check:
#  - Check the path that I send to Ext2.open(), because I think it is assumed that
#    we must put the 'name' of the partition (which would represent the root directory '/')
#    followed by what we want to open (but we can even put anything, or directly nothing;
#    I have to test that well). In Windows it would be for example C:\ ..., being C: the name/label
#    of the volume/partition (or the mount point), it would be necessary to see what format it is in Linux (it could be sda1/...).
#  - I could implement the methods that I left defined at the end of the 'superblock.py' and 'inode.py' files.

# NOTE: Whenever we speak about a "block number" or "inode number", it is spoken in an absolute way, that is,
#       that block or inode number in the entire filesystem (and if it is relative to something, it will be specified).
#       The blocks are counted from the boot area to the end of the partition, and the inodes are counted for each entry
#       in the inode table of each block group.

from . import directory_entry
from . import group_descriptor
from . import inode
from . import superblock

import struct
from math import ceil

# Constants representing sizes in bytes
DISK_SECTOR_SIZE        = 512

SB_STRUCT_SIZE          = 1024
GD_STRUCT_SIZE          = 32
# INODE_STRUCT_SIZE       = 128
#   this value actually depends on the revision of ext2
#       rev. 0: always 128 bytes
#       rev. 1: must be a perfect power of 2 and must be smaller or equal to the block size
#   anyway, at the moment I only parse the first 128 bytes of the inode (in 'Inode.py'), which is the base size of any inode
#   but I need the exact value to correctly read the inodes from the disk (I get this value from the superblock, see Ext2's constructor).
DENTRY_STRUCT_BASE_SIZE = 8

# Encoding of filenames and paths
ENCODING = 'latin-1'

class Directory:
    """
    A directory is actually an inode whose data blocks that it points to,
    contain directory entries.
    What I do with this class is get to those blocks and parse them.

    :param filesystem: the base filesystem (of class Ext2) to which the Directory belongs
    :param inode_obj: the inode (Inode object) that represents the directory
    :param name: the directory name (it does not come from its inode, but from some directory entry of its parent directory)
    :param parent: the parent (Directory object) of the (new) directory, used to build a path string
    """
    def __init__(self, filesystem, inode_obj, name, parent=None):
        
        self.filesystem = filesystem
        self.inode_obj = inode_obj
        self.name = name

        self.files = []

        if parent is None:
            self.path = self.name.decode(ENCODING) # for the root, 'name' will be the 'volume_name'.
        else:
            self.path = parent.path + '/' + self.name.decode(ENCODING)

        self._parse()

    def __repr__(self):
        # a bit of a hack (X or Y) in case we want to show the root directory,
        # and it doesn't have a certain name (volume_name == "" (empty))
        return f"< Directory {self.path or '/'} >"

    def __str__(self):
        ret = f"< Directory {self.path or '/'} >\n"
        ret += "---------------------------------FILES------------------------------------\n"
        for f in self.files:
            ret += f"{f.name.decode(ENCODING):50} ({f.file_type})\n"
        ret += "--------------------------------------------------------------------------\n"
        return ret

    def _read_dentries(self, block_number):
        """
        Internal method that reads and parses the directory entries of a block
        in the filesystem. It adds DirectoryEntry objects to the list of files
        of the current Directory object.
        """

        raw_block = self.filesystem.read_block(block_number)

        offset = 0 # this variable will store the starting address of each directory entry
        block_size = self.filesystem.superblock.s_log_block_size
        # let's read and parse the directory entries (the last valid entry points to the end of the block)
        while offset < block_size:
            dx = offset + DENTRY_STRUCT_BASE_SIZE
            file = directory_entry.DirectoryEntry(raw_block[offset:dx]) # we parse the first 8 bytes (the constant part of the dentry).
            file.name = raw_block[dx:dx+file.name_len] # and now the rest, corresponding to the name (the variable part).
            if file.inode != 0:
                # This happens only if the first file is deleted;
                # all other deleted file entries will be skipped due to
                # a proper rec_len of the previous entry.
                # (file deleted -> prev. rec_len points to next dentry, and inode=0)
                self.files.append(file)
            offset += file.rec_len

    def _parse(self):
        """
        Method that parses the pointers of the direct and indirect blocks pointed by
        the inode that represents a directory, in order to obtain the number of each
        data block assigned to the directory and parse the directory entries they contain.
        """

        # let's read the direct blocks
        direct_blocks = self.filesystem._parse_direct_blocks(self.inode_obj.i_block[0:12])
        for directory_block_number in direct_blocks:
            self._read_dentries(directory_block_number)

        # and now the indirect blocks
        if self.inode_obj.i_block[12] != 0: # thus, we avoid reading the block '0' (*)
            indirect_1_block = self.filesystem._parse_indirect_1_block(self.inode_obj.i_block[12])
            for directory_block_number in indirect_1_block:
                self._read_dentries(directory_block_number) # we read the directory entries contained in the blocks pointed to by the pointers of indirect_1_block.

        if self.inode_obj.i_block[13] != 0:
            indirect_2_block = self.filesystem._parse_indirect_2_block(self.inode_obj.i_block[13])
            for directory_block_number in indirect_2_block:
                self._read_dentries(directory_block_number)

        if self.inode_obj.i_block[14] != 0:
            indirect_3_block = self.filesystem._parse_indirect_3_block(self.inode_obj.i_block[14])
            for directory_block_number in indirect_3_block:
                self._read_dentries(directory_block_number)


        # *: Since a pointer pointing to block 0, means null pointer.
        #    As the filesystem allocates new blocks to the directory/file, the pointers will no longer be null.
        #    If we read block 0, we would be reading the boot area or boot area + superblock, depending on the block_size.
        #
        #    And when we analyze the indirect blocks, there will be no problem of 0's
        #    because we will filter them. In addition, that an indirect pointer of
        #    the inode is !=0, it means that there will be minimally a sequence of
        #    non-null pointers and there will be no problem of 0's.
        #    (for example, if i_block[14] != 0, it means that there is at least
        #    one data block assigned to the file at the end of
        #    triple_block -> double_block -> simple_block -> data_block)

        # NOTE: Although I store in variables the list of the numbers of data blocks
        #       that contain the directory entries, they are local to this internal method,
        #       so when finished, they are 'freed' of memory, those references are not preserved
        #       (I say this due to the magnitude of bytes that we could have, since each block is referenced by a 4-byte pointer).

    def show_dentries(self):
        """
        Method that returns a string with the representation of each
        DirectoryEntry object that contains the list of files in the directory.
        """
        ret = f"< Directory {self.path or '/'} >\n"
        ret += "----------------------------DIRECTORY-ENTRIES-----------------------------\n"
        for f in self.files:
            ret += f"{str(f)}\n"
        ret += "--------------------------------------------------------------------------\n"
        return ret

    def show_inode(self):
        """
        Method that returns a string with the representation of the Inode object
        associated with the directory.
        """
        ret = f"< Directory {self.path or '/'} >\n"
        ret += "-----------------------------ASSOCIATED-INODE-----------------------------\n"
        ret += f"{str(self.inode_obj)}"
        ret += "--------------------------------------------------------------------------\n"
        return ret


class FileHandle:
    """
    Class that handles a data file, given its inode that represents it.
    It will have the basic file operations: read, write, seek, close ...
    (the 'open' would be implemented in the Ext2 class, since it just returns
    this FileHandle object, as when we make a true open in Python or another language).
    At the moment, the 'write' will not be implemented.

    :param filesystem: the base filesystem (of class Ext2) to which the file belongs
    :param inode_obj: the inode (Inode object) that represents the file
    :param name: the file name (it does not come from its inode, but from some directory entry of its parent directory)
    :param parent: the directory (Directory object) that "contains" the file, used to build a path string
    """
    def __init__(self, filesystem, inode_obj, name, parent=None):
        
        self.filesystem = filesystem
        self.inode_obj = inode_obj
        self.name = name

        if parent is None:
            self.path = self.name.decode(ENCODING) # for the root, 'name' will be the 'volume_name'.
        else:
            self.path = parent.path + '/' + self.name.decode(ENCODING)

        self.closed = False # I should put this attribute as 'private' through properties.

        # We will always keep the file's bytes in a 'buffer',
        # one block at a time (starting with its first block)
        self._buffer      = self.filesystem.read_block(self.inode_obj.i_block[0])
        self._buffer_pos  = 0 # 0 <= pos < buffer_size
        self._buffer_size = self.filesystem.superblock.s_log_block_size

        # We keep the pointer to the last 'buffered' block (block number relative to the file),
        # so that in the next reading of the file, we know where we are.
        # (remember that we will implement a 'true' read, that is, we can read
        # a file on different occasions and the byte pointer will move)
        self._current_block_pointer = 0

        # position in the file (pointer to the byte number), .tell() returns this
        self._file_pos = 0 # 0 <= pos < self.inode_obj.i_size

        # We obtain in advance all the block numbers that are assigned to the file
        # (I don't think it is the most efficient in terms of memory, but it makes the 'read' method much easier)
        # (remember that each block is referenced by a 4-byte pointer, so 4*len(list) could be very large)
        # (here we can see different maximum sizes in blocks of a file: https://www.nongnu.org/ext2-doc/ext2.html#def-blocks)
        self._data_block_numbers = []
        self._data_block_numbers = self.filesystem._parse_direct_blocks(self.inode_obj.i_block[0:12])
        if self.inode_obj.i_block[12] != 0: # thus, we avoid reading the block '0' (just like in the class Directory)
            self._data_block_numbers += self.filesystem._parse_indirect_1_block(self.inode_obj.i_block[12])
        if self.inode_obj.i_block[13] != 0:
            self._data_block_numbers += self.filesystem._parse_indirect_2_block(self.inode_obj.i_block[13])
        if self.inode_obj.i_block[14] != 0:
            self._data_block_numbers += self.filesystem._parse_indirect_3_block(self.inode_obj.i_block[14])
        # the 'end of file' is defined by the length of this list (the last position would be its last data block).

    def __repr__(self):
        return f"< FileHandle for {self.path} >"
    
    def __str__(self):
        return self.__repr__()

    def close(self):
        """
        Closes the file.
        """
        if self.closed == True:
            raise ValueError("I/O operation on closed file.")

        self.closed = True

        return True

    def read(self, size=-1):
        """
        Method that reads a certain number of bytes (size) from the file
        referenced by the FileHandle object (as long as the file is 'open').
        If the 'size' argument is omitted, the entire file will be read
        (or the remaining bytes of it depending on the position of its pointer).
        """
        if self.closed == True:
            raise ValueError("I/O operation on closed file.")

        if size < 0: # it would indicate that we want to read the remaining bytes of the file.
            size = self.inode_obj.i_size - self._file_pos # file length in bytes - current position of the file pointer.

        ret = [] # here we will store the byte strings that we read from the buffer, and in the end we will join everything.

        # while it is necessary to read a next block of the file to satisfy the reading, and we are not already in its last block (end of file)...
        while size > (self._buffer_size - self._buffer_pos) and self._current_block_pointer+1 < len(self._data_block_numbers): # len is O(1)
            ret.append(self._buffer[self._buffer_pos:]) # here we start from 'buffer_pos' in case it was read a little first (and we did not enter this 'while'), and then a lot (and we did enter).
            size           -= self._buffer_size - self._buffer_pos # we are subtracting from 'size' the number of bytes that we already read.
            self._file_pos += self._buffer_size - self._buffer_pos # we advance the file pointer as we read.
            self._buffer_pos = 0 # as we consume the entire buffer, we set its position to 0.
            next_block_pointer = self._current_block_pointer + 1
            next_block_number = self._data_block_numbers[next_block_pointer]
            self._buffer = self.filesystem.read_block(next_block_number) # we read the next data block and load it into the buffer.
            self._current_block_pointer = next_block_pointer

        span = min(self.inode_obj.i_size - self._file_pos, size) # We do this to avoid reading more bytes from the buffer than the remaining bytes of the file.
        ret.append(self._buffer[self._buffer_pos:self._buffer_pos+span]) # we read the X ('span') bytes from the buffer
        self._buffer_pos += span # and we move the pointers of both the buffer and the file.
        self._file_pos   += span # (there will be no overflow problems because 'span' will always be smaller than the block size)
        return b"".join(ret)

            # I have to check what to do if trying to read more bytes than the file has. DONE
            # (there will come a time when we reach the last block, the while will be cut there,
            # and the 'span' will be left with the right amount of bytes that remain to be read)
            # (as in Python, it reads up to where there are bytes and that's it. And if we continue to want to read later, it returns b'' [empty])
            
            # And also what would happen if I read a few bytes at a time, avoiding entering to the while,
            # and there comes a time that I go over of the block size; since I would need to read the following block. DONE
            # (this is solved by checking in the while '(self._buffer_size - self._buffer_pos)',
            # thanks to the position of the pointer we will know when it will be necessary to go to the next block,
            # and in those cases we enter to the while, since 'size' will be greater than that difference)

            # I would have to check what happens if I have already read the entire file, and I want to read such a large number of bytes
            # that it goes into the while, because there, an extra append would be made with what was left in the buffer. DONE
            # (It would not enter the while because the second condition would give 'false'; we will have stayed in the position of its last block).

    def seek(self, offset, whence=0):
        """
        Moves the file pointer, based on 'offset'.
        The 'whence' argument is optional and defaults to 0, which means absolute file positioning,
        other values are 1 which means seek relative to the current position,
        and 2 means seek relative to the file's end.
        Returns the current position of the file pointer, after moving.
        """
        
        if self.closed == True:
            raise ValueError("I/O operation on closed file.")

        if whence == 0:
            new_file_pos = offset
        elif whence == 1:
            new_file_pos = self._file_pos + offset
        elif whence == 2:
            new_file_pos = self.inode_obj.i_size + offset # the 'offset' is expected to be negative
        else:
            raise ValueError(f"invalid whence ({whence}, should be 0, 1 or 2)")

        # The idea is to calculate the number of blocks that the new ABSOLUTE position
        # of the file pointer represents (always starting the count from the beginning of the file).
        # As we have previously loaded each data block number of the file (self._data_block_numbers),
        # we can directly obtain the block where the new position falls, and thus load it into the buffer.

        if new_file_pos >= self.inode_obj.i_size:       # If we want to go beyond the end of the file
            block_number = self._data_block_numbers[-1] # we will keep its last block
            self._buffer_pos = self._buffer_size        # and move the buffer pointer to the end of the buffer
            self._file_pos = self.inode_obj.i_size      # and the file pointer at the end of the file.
            self._current_block_pointer = len(self._data_block_numbers) - 1 # We update this attribute for a future 'read()'.
        elif new_file_pos < 0:
            block_number = self._data_block_numbers[0] # A similar analysis if we want to go further back of the beginning of the file..
            self._buffer_pos = 0
            self._file_pos = 0
            self._current_block_pointer = 0
        else:
            block_index = new_file_pos // self._buffer_size       # Else, we get how many blocks of the file the offset covers,
            block_number = self._data_block_numbers[block_index]  # we keep the data block number obtained from the calculated quantity
            self._buffer_pos = new_file_pos % self._buffer_size   # we move the buffer pointer the remaining amount of bytes
            self._file_pos = new_file_pos                         # and the file pointer should be the offset.
            self._current_block_pointer = block_index             # We update this attribute for a future 'read()'.
        
        self._buffer = self.filesystem.read_block(block_number) # Finally we update the buffer with the reading of the obtained block.
        
        return self._file_pos

        # NOTA: I assume that in the list of data_block_numbers there would be no 'gaps' (0's) in between.
        #       I don't know if it's possible *, but if it happens, this would fail
        #       since data_block_numbers[block_index] would be out of date.
        #       (* that is, I don't know if it is possible for a data block, to be deallocated from the file,
        #       leaving a pointer to null (->0) in between, and then the inode pointers are not 'defragmented', or not 'compact')

    def tell(self):
        """
        Returns the current position of the file pointer.
        """
        if self.closed == True:
            raise ValueError("I/O operation on closed file.")

        return self._file_pos

    def show_inode(self):
        """
        Method that returns a string with the representation of the Inode object
        associated with the file.
        """
        ret = f"< File {self.path} >\n"
        ret += "-----------------------------ASSOCIATED-INODE-----------------------------\n"
        ret += f"{str(self.inode_obj)}"
        ret += "--------------------------------------------------------------------------\n"
        return ret


class Ext2:
    """
    Class that handles an ext2 filesystem.

    :param path: It is the way to access the storage device.
        On Windows, it is in the format: r"\\.\PhysicalDriveX", and on Linux "/dev/sdX".
    :param base_address: It is the offset (byte number), inside the device, where
        the partition (with an ext2 fs) that we want to analyze, begins.
    """
    def __init__(self, handle, base_address):
        """
        The storage device is opened.
        The byte pointer is positioned at the beginning of the desired partition.
        And the boot area, the superblock (original), the group descriptor table
        (original) and the root inode, are read.
        """
        self.base_address = base_address

        self.handle = handle # read-only for now (for security, I should set this attribute as private through properties)
        self.handle.seek(self.base_address)

        # the first 2 sectors of the partition correspond to the boot area (are unused by the ext2 filesystem).
        self.boot_area = self.handle.read(DISK_SECTOR_SIZE*2)
        # the next 1024 bytes correspond to the original superblock (we are already within block group 0).
        self.superblock = superblock.Superblock(self.handle.read(SB_STRUCT_SIZE))
        # and then there will be as many group descriptors as there are block groups in the filesystem.
        # (the group descriptor table begins at the block following the superblock)
        self.handle.seek(self.base_address + self.superblock.s_log_block_size * (self.superblock.s_first_data_block + 1))
        useful_blocks = self.superblock.s_blocks_count - self.superblock.s_first_data_block # if block_size=1K, the first block doesn't belong to the first block_group
        block_group_count = ceil(useful_blocks / self.superblock.s_blocks_per_group) # (*1)
        self.group_descriptors = [group_descriptor.GroupDescriptor(self.handle.read(GD_STRUCT_SIZE)) for i in range(block_group_count)] # (*2)

        # we get the inode size, since it is not always 128 bytes.
        self.INODE_STRUCT_SIZE = self.superblock.s_inode_size

        # The root directory always corresponds to inode No. 2 (inode_table[1]), which belongs to block group No. 1 (bg[0]).
        # (note: I don't use the 'read_inode' method cause for me in this case it is more descriptive to see the read_record's arguments)
        inode_table_block = self.group_descriptors[0].bg_inode_table
        raw_root_inode_entry = self.read_record(inode_table_block, self.INODE_STRUCT_SIZE, offset=self.INODE_STRUCT_SIZE)
        root_inode = inode.Inode(raw_root_inode_entry)
        self.root = Directory(self, root_inode, name=self.superblock.s_volume_name)

        # NOTE 1: When I calculate block_group_count, I round up to the upper integer (*) because apparently the free space
        #         at the end of the partition is assigned to one more 'block group', but which obviously does not respect having
        #         'superblock.s_blocks_per_group' blocks, but less.
        #         (anyway, this is by way of comment, as I did it works as I wanted, I don't think the logic needs to be changed)

        # NOTE 2: Maybe all the calculations referring to the number of block groups, should go in the class Superblock.
        #         (due to what I do in the __str__ and in the 2 lines prior to make the list of group descriptors*).

    def __repr__(self):
        return f"< ext2 @ {self.base_address} of {self.path}>\n"

    def __str__(self):
        # NOTE: The filesystem is divided into blocks as follows:
        #       boot_area + (total_blocks - 1 // blocks_per_group)*blocks_per_group + (total_blocks-1 % blocks_per_group)
        #       OR if block_size > 1K:
        #       (total_blocks // blocks_per_group)*blocks_per_group + (total_blocks % blocks_per_group)
        useful_blocks = self.superblock.s_blocks_count - self.superblock.s_first_data_block
        last_block_group_len = useful_blocks % self.superblock.s_blocks_per_group
        aux = f" (the last one has {last_block_group_len} blocks assigned)"
        if last_block_group_len == 0:
            # all block groups have fitted perfectly
            aux = ""

        return (
                f"< ext2 Filesystem:\n"
                f"{'Number of block groups:':49}{len(self.group_descriptors)}{aux}\n"
                f"{self.superblock}>\n"
            )

    def read_record(self, block_number, length, offset=0):
        """
        Method that reads a certain amount of bytes (length) from a given block
        of the filesystem (block_number), starting from an offset (by default 0).
        """
        block_size = self.superblock.s_log_block_size
        address = block_number*block_size             # This number will be multiple of 512 as 'block_size' is.
        self.handle.seek(self.base_address + address) # 'base_address' is also multiple, since it must be the sector of the device where the partition begins.
        for i in range(offset//block_size):           # I do this mostly for very large offset cases*
            self.handle.seek(block_size, 1)
        # here I have to do a 'read' to move the device's pointer, because if I did a seek, the next read could give an error for just not being positioned in a multiple of 512.
        self.handle.read(offset % block_size)         # *and then this read is small: it will be less than the block size (<= block_size-1),
        raw_record = self.handle.read(length)
        return raw_record

        # Testing, I discovered that there are some 'restrictions' when wanting
        # to read something from a storage device* (this is already outside the filesystem).
        # We can only read if we are positioned (seek) in a multiple of 512 bytes.
        # Once there, we make a first reading, and then we will have the next 8192 bytes
        # enabled/allowed to do some seek in that interval and perform a read without problems.
        # (Even if the read goes beyond that limit later, there is no problem with that).
        # Otherwise, an exception will be thrown when trying to read something.

        # Therefore, I replace a seek(offset) with a read(offset); it is not very nice but it works.
        
        # * NOTE: For 'normal' files, this problem does not arise, therefore we could analyze
        #         for example a disk image (.vhd) without worrying much about all this.

    def read_block(self, block_number):
        """
        Method that reads a block from the filesystem (block_number >= 0).
        """
        block_size = self.superblock.s_log_block_size
        address = block_number*block_size
        self.handle.seek(self.base_address + address) # here everything goes well, because it is guaranteed that we will be in a multiple of 512 bytes.
        raw_block = self.handle.read(block_size) # therefore this read does not give problems.
        return raw_block

        #block_size = self.superblock.s_log_block_size
        #self.handle.seek(self.base_address)
        #for i in range(block_number):
        #    self.handle.seek(block_size, 1)
        #raw_block = self.handle.read(block_size)
        #return raw_block

    def read_inode(self, inode_number):
        """
        Method that reads an inode from the filesystem (inode_number >= 1).
        Attention! Unlike block numbering, the inodes start to be numbered from 1,
        since inode number 0 indicates 'null inode' (so the first entry in
        the inode table 'inode_table[0]', corresponds to inode 1 and not inode 0).
        """
        if inode_number < 1:
            raise TypeError("the inode number must be >= 1 !")
        # locating the inode
        block_group = (inode_number - 1) // self.superblock.s_inodes_per_group
        first_inode_table_block = self.group_descriptors[block_group].bg_inode_table
        local_inode_index = (inode_number - 1) % self.superblock.s_inodes_per_group
        # and now we read it
        raw_inode = self.read_record(first_inode_table_block, self.INODE_STRUCT_SIZE, offset=local_inode_index*self.INODE_STRUCT_SIZE)
        return raw_inode

    def _parse_direct_blocks(self, pointers):
        """
        Method that parses a list of direct pointers to data blocks.
        We already have the number of each data block, but what I do is filter
        the pointers to null blocks (p-> 0).
        """
        data_block_numbers = [pointer for pointer in pointers if pointer != 0]
        return data_block_numbers
        # There may be unallocated blocks yet (pointers to 0), so we will only keep those pointers that do not equal to null (0).

    def _parse_indirect_1_block(self, block_number):
        """
        Method that parses the pointers contained in a simple indirect block,
        given its block number within the filesystem. By containing direct pointers,
        we directly obtain all the numbers of data block that indirectly points.
        """
        raw_indirect_1_block = self.read_block(block_number)
        indirect_1_block = [pointer[0] for pointer in struct.iter_unpack("<I", raw_indirect_1_block) if pointer[0] != 0]
        return indirect_1_block
        # Each pointer occupies 4 bytes, therefore each indirect block will have block_size/4 pointers to other blocks.

    def _parse_indirect_2_block(self, block_number):
        """
        Method that parses the pointers contained in a double indirect block,
        given its block number within the filesystem. By containing pointers
        that point to simple indirect blocks, we will use the '_parse_indirect_1_block'
        method for each of them, and thus obtain all the data block numbers
        that are pointed at the end of this indirection chain.
        """
        raw_indirect_2_block = self.read_block(block_number)
        indirect_2_block = [pointer[0] for pointer in struct.iter_unpack("<I", raw_indirect_2_block) if pointer[0] != 0]
        
        data_block_numbers = []

        for p in indirect_2_block:
            data_block_numbers += self._parse_indirect_1_block(p)

        return data_block_numbers

    def _parse_indirect_3_block(self, block_number):
        """
        Method that parses the pointers contained in a triple indirect block,
        given its block number within the filesystem. By containing pointers
        that point to double indirect blocks, we will use the '_parse_indirect_2_block'
        method for each of them, and thus obtain all the data block numbers
        that are pointed at the end of this indirection chain.
        """
        raw_indirect_3_block = self.read_block(block_number)
        indirect_3_block = [pointer[0] for pointer in struct.iter_unpack("<I", raw_indirect_3_block) if pointer[0] != 0]
        # how much power in a single line of code! it's beautiful, Python at its best!

        data_block_numbers = []

        for p in indirect_3_block:
            data_block_numbers += self._parse_indirect_2_block(p)

        return data_block_numbers


    def open(self, path):
        """
        Method that "opens" a file or directory on the filesystem.
        It returns an object of type "Directory" or "FileHandle" depending on
        what we are looking for (according to what we specify in the 'path',
        which must be absolute!).
        With the returned object, we can make use of its methods to see
        the content of a directory, or the data of a file, as appropriate
        (among other things).
        """
        path = path.encode(ENCODING) # ext2 is case sensitive, so I handle the path as it comes.
        parts = path.split(b'/')[1:] # we decompose the path in a list with the directory/file names.
        obj = self.root # we always start from the root directory.
        if path != b'/': # in case we want to open only the root.
            for name in parts: # We will go into directory by directory until we reach the file or directory we are looking for.
                try:
                    # we make a dictionary <name: inode> from the directory entries of the current directory.
                    files = {f.name:f.inode for f in obj.files}
                except AttributeError:
                    # in case something like this happens: /dir_1/file.txt/dir_2
                    # a file can only be at the end of the path, not in the middle (everything else must be directories).
                    raise FileNotFoundError(f"{obj.path} is not a Directory!") # we will see this exception by console.
                if name in files: # we verify that the searched directory/file name is in a directory entry of the current directory.
                    # We locate, read and parse the inode
                    inode_number = files[name]
                    raw_inode = self.read_inode(inode_number)
                    inode_obj = inode.Inode(raw_inode)
                    # and we instantiate the directory or file as of the inode that represents it.
                    if inode_obj.i_mode[0] == 'd': # Maybe this way of checking the file type needs to be improved.
                        obj = Directory(self, inode_obj, name, parent=obj)
                    else:
                        obj = FileHandle(self, inode_obj, name, parent=obj) # if we get here before finishing the 'for', the exception 'AttributeError' will be thrown above.
                else:
                    raise FileNotFoundError(f"No such file or directory {obj.path}/{name.decode(ENCODING)}")
            
        return obj

    # I don't know if it's the proper method name, but I wanted to put the 'close' here.
    def unmount(self):
        self.handle.close()
        return True
