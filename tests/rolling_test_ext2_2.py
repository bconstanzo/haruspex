"""
Testing the handling of a real Ext2 filesystem.
"""

import haruspex

# We open a storage device and obtain through its MBR (in this case),
# the starting sector of the desired partition.
fd = open(r"\\.\PhysicalDrive1", "rb")
data = fd.read(512)
mbr = haruspex.mbr.Table(data)
part = mbr.partitions[0]
# and the ext2 filesystem is instantiated
fs = haruspex.ext2.ext2.Ext2(r"\\.\PhysicalDrive1", part.start * 512)

print(fs) # we will show part of the superblock

for gd in fs.group_descriptors[0:3]: # we show the first three group descriptors
    print(gd)

print(fs.group_descriptors[-1]) # we show the last group descriptor

root_dir = fs.open("/")
print(root_dir) # files of root directory
print(root_dir.show_dentries()) # the actual representation of each directory entry in the root directory
print(root_dir.show_inode()) # the representation of the root directory inode

file = fs.open("/dir1/foo.txt")
print(file) # internal representation of the FileHandle object
print(file.show_inode()) # we show the inode that represents the file
print(file.read(7))
print(file.read())
print(file.seek(7))
print(file.read())
print(file.tell())
print(file.close())

print("")
print(fs.read_block(1)) # we show the raw content of block 1 of the filesystem
print("")
print(fs.read_inode(2)) # we show, in raw, the inode 2 of the filesystem
print("")

print(fs.unmount()) # for now it only 'closes' the 'handle' of the storage device
