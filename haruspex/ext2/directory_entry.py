# To check:
#  - nothing else for now.

import struct

# Types of files recognized by Ext2
file_types = {
    0: "Unknown",
    1: "Regular file",
    2: "Directory",
    3: "Character device",
    4: "Block device",
    5: "Named pipe",
    6: "Socket",
    7: "Symbolic link"
}

# Filename encoding
ENCODING = 'latin-1' # generally latin-1 is used

class DirectoryEntry:
    """
    Class representing a Directory Entry of an ext2 filesystem.
    (are the records stored in the directory blocks pointed to by directory inodes)
    (I call them 'directory blocks', but they count as data blocks of the filesystem)

    The structure has a variable length, since the 'name' field is a
    variable length array of up to 255 characters. Moreover, the length of a
    directory entry is always a multiple of 4 and, therefore, null characters ('\0')
    are added for padding at the end of the filename, if necessary.
    (but the 'name_len' field stores the actual file name length)
    """
    def __init__(self, data=bytes(8),
                 inode=None, rec_len=None, name_len=None, file_type=None, name=None
                 ):

        # let's parse
        p_inode     = struct.unpack("<I", data[0:4])[0]
        p_rec_len   = struct.unpack("<H", data[4:6])[0]
        p_name_len  = struct.unpack("<B", data[6:7])[0]
        p_file_type = struct.unpack("<B", data[7:8])[0]
        # I directly assign the raw binaries to it and then in the '__str__' I make it a 'decode'.
        p_name      = data[8:8+p_name_len] # variable length
        # note: by default, the 'slice' will return b'' (empty bytestring) and not IndexError

        self._raw_data = data
        # and now we set, either the parameterized values or the parsed ones
        self.inode     = inode     or p_inode
        self.rec_len   = rec_len   or p_rec_len
        self.name_len  = name_len  or p_name_len
        self.file_type = file_type or p_file_type
        self.name      = name      or p_name

    @property
    def raw_data(self):
        """
        Bytes to be parsed.
        (are the [8 to n] bytes corresponding to the structure of a directory entry)
        """
        return self._raw_data

    @raw_data.setter
    def raw_data(self, value):
        pass
    
    # ---

    @property
    def inode(self):
        """
        Inode number representing the file or directory
        """
        return self._inode

    @inode.setter
    def inode(self, value):
        # This way we prevent someone from sending us data types that do not have
        # a numerical representation. That is, in those cases, an exception will be thrown.
        self._inode = int(value)

    @property
    def rec_len(self):
        """
        Directory entry length (in bytes)
        """
        return self._rec_len

    @rec_len.setter
    def rec_len(self, value):
        self._rec_len = int(value)

    @property
    def name_len(self):
        """
        Filename length
        """
        return self._name_len

    @name_len.setter
    def name_len(self, value):
        self._name_len = int(value)

    @property
    def file_type(self):
        """
        Returns a string corresponding to the file type
        """
        return file_types[self._file_type]

    @file_type.setter
    def file_type(self, value):
        value = int(value)
        # to avoid a KeyError
        if value < 0 or value > 7:
            value = 0
        self._file_type = value

    @property
    def name(self):
        """
        Filename (up to 255 chars)
        """
        return self._name

    @name.setter
    def name(self, value):
        # I admit both strings and bytestrings, but internally I keep bytestrings.
        if isinstance(value, str):
            value = bytes(value, ENCODING)
        self._name = value

    # ---

    def __str__(self):
        return (
                f"Inode number:           {self.inode}\n"
                f"Directory entry length: {self.rec_len}\n"
                f"Filename length:        {self.name_len}\n"
                f"File type:              {self.file_type}\n"
                f"Filename:               {self.name.decode(ENCODING)}\n"
            )

