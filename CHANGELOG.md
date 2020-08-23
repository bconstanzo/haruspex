## 0.3
+ Write capabilities:
  + Dump a FileRecord to bytes.
  + Modify a Directory or FileHandle's associated record.
  + Create a new FileRecord on disk/Directory.
  + Allocate and free clusters on the FATs

## 0.2.2
* Fixes a .seek() bug in FileHandle where it wasn't working for multi-clustered
  files.
* 0.2.1 fixed a FAT32-timestamp reading bug.

## 0.2
* Should be enough for a simple introduction to filesystems:
  * Parsing a partition table (MBR for now).
  * Parsing file records from a FAT32 filesystem.
  + Parsing the FAT32 structures to read from the filesystem:
    * Reading the filesystem header and structures
    * Reading files.
    * Reading directories.
  * Have a comfortable API to use from a console.

## 0.1
* Initial version uploaded to PyPI.