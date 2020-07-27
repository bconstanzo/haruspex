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
fh = haruspex.fat32.FileHandle(fs, record, "rb")

print(mbr)
print(fs)
print(fh)

# What we tested of FileHandle:
# * Reading a specific file.
# * Seeking and reading.
# * Seeking past the end.
# * Reading all and reading againg (empty)
# * Seeking past the end and reading (empty)