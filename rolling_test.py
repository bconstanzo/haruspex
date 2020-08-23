import haruspex

fd = open("test_files/virtual.vhd", "rb")
data = fd.read(512)
mbr = haruspex.mbr.Table(data)
part = mbr.partitions[0]
fs = haruspex.fat32.FAT32("test_files/virtual.vhd", part.lba_start * 512)
while data:
    if b"TXT" in data:
        break
    data = fd.read(512)
record = haruspex.fat32.FileRecord(data[128:160])
dir_       = haruspex.fat32.Directory(fs, fs.root.files[3])
fh_text    = haruspex.fat32.FileHandle(fs, record, "rb")
fh_caracol = haruspex.fat32.FileHandle(fs, dir_.files[2], "rb")

print(mbr)
print(fs)
print(fh_text)
print(fh_caracol)

# What we tested of FileHandle:
# * Reading a specific file.
# * Seeking and reading.
# * Seeking past the end.
# * Reading all and reading againg (empty)
# * Seeking past the end and reading (empty)