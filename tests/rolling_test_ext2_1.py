"""
Testing the parsing of Ext2 structures.
"""

from haruspex import ext2

#import struct

# Superblock parser (1024 bytes)
raw_superblock = """
7b 00 00 00 c8 00 00 00 05 00 00 00 32 00 00 00 14 00 00 00 01 00 00 00 02 00 00
00 fe ff ff ff 0a 00 00 00 0a 00 00 00 07 00 00 00 16 45 3d 60 02 00 00 00 03 00
04 00 53 ef 00 00 07 00 08 00 09 00 00 00 0a 00 00 00 00 00 00 00 0c 00 00 00 0d
00 0e 00 0f 00 00 00 10 00 11 00 12 00 00 00 13 00 00 00 14 00 00 00 01 02 03 04
05 06 07 08 09 0a 0b 0c 0d 0e 0f 10 70 72 75 65 62 61 5f 73 70 5f 65 78 74 32 00
00 2f 6d 6e 74 2f 73 64 61 31 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 15 00 00 00 16 17 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
""".replace("\n", "")
superblock_data = bytes.fromhex(raw_superblock)

# this data comes from doing:
#    superblock_data = struct.pack("<IIIIIIIiIII", 123, 200, 5, 50, 20, 1, 2, -2, 10, 10, 7)
#    superblock_data += struct.pack("<IIHHHHHHIIIIHH", 1614628118, 2, 3, 4, 61267,
#                                    0, 7, 8, 9, 10, 0, 12, 13, 14)
#    superblock_data += struct.pack("<IHHIIIBBBBBBBBBBBBBBBB", 15, 16, 17, 18, 19, 20,
#                                    1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16)
#    superblock_data += b'prueba_sp_ext2\x00\x00'
#    superblock_data += b'/mnt/sda1' + bytes(55)
#    superblock_data += struct.pack("<IBBH", 21, 22, 23, 0)
#    superblock_data += bytes(204*4)
sb = ext2.superblock.Superblock(superblock_data)
"""Another way: sb = Superblock(s_log_block_size=1, s_state=1, s_creator_os=4)"""
print(sb)

# Group descriptor parser (32 bytes)
raw_gd = """
03 00 00 00 04 00 00 00 05 00 00 00 32 00 14 00 28 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00
""".replace("\n", "")
gd_data = bytes.fromhex(raw_gd)
# gd_data = struct.pack("<IIIHHHHIII", 3, 4, 5, 50, 20, 40, 0, 0, 0, 0)
gd = ext2.group_descriptor.GroupDescriptor(gd_data)
"""Another way: gd = GroupDescriptor(bg_inode_bitmap=999, bg_free_inodes_count=7)"""
print(gd)

# Inode parser (128 bytes, but it could be a larger value depending on the revision of ext2)
raw_inode = """
ec 41 7b 00 00 00 10 00 00 00 00 00 e5 c1 2e 60 30 2a 00 00 00 00 00 00 db 03 0a
00 bc 02 00 00 a0 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 07 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 05 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
""".replace("\n", "")
inode_data = bytes.fromhex(raw_inode)
# inode_data = struct.pack("<HHIIIIIHHIIIIIIIIIIIIIIIIIIIIIIIII", 16876, 123, 2**20,
#                          0, 1613677029, 3600*3, 0, 987, 10, 700, 416, 0, 0, 0, 0,
#                          1, 0, 0, 0, 0, 7, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0)
ind = ext2.inode.Inode(inode_data)
"""Another way: ind = Inode(i_mode=0x8fff, i_atime=1614745834, i_flags=0b1000000000000)"""
print(ind)

# Directory entry parser (8 to n bytes)
raw_dentry = "43 00 00 00 0c 00 03 02 75 73 72 00"
dentry_data = bytes.fromhex(raw_dentry)
# dentry_data = struct.pack("<IHBB", 67, 12, 3, 2)
# dentry_data += b'usr\0'
de = ext2.directory_entry.DirectoryEntry(dentry_data)
"""Another way: de = DirectoryEntry(rec_len=30, file_type=1, name="föò.txt")"""
print(de)
