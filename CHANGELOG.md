## 0.5 (WIP, previosly 0.4, partial changes are in place)
+ Write capabilities:
  * Write/modify partition tables.
  + Dump a FAT32 FileRecord to bytes.
  + Modify a Directory or FileHandle's associated record.
  + Create a new FileRecord on disk/Directory.
  + Allocate and free clusters on the FATs.
+ Added keyword-only arguments for object creation to override the parsed
  values. This is mainly a QOL improvement when creating new structures.
  + Now you can also complete ignore the data argument, and it defaults to an
    empty bytes object of the corresponding length. Thus, it's now easier to
    create new structures from scratch.

## 0.4.2
* Changed the interface to instantiate filesystems, now they receive an open
  file-like instead of a path.
  * This allows working over zipped images on Python 3.7+.
  * This is part of the roadmap for some more thorough testing.
* Added bits of NTFS that allows basic data carving:
  * $FILENAME and $STANDARD_INFORMATION structures
  * $I30 files (for directory indexes) support
* We're starting to move out from Python 3.6, as it reaches EOL. We'll do a
  little effort to avoid relying on 3.7+ functionalities if possible, but
  in the future 3.6 support will be deprecated.

## 0.4.0
* Added enzoski as contributor! Welcome Enzo!
* ext2 support (by enzoski).
* Few bugfixes (check history for details).
* Som QOL improvements from 0.5 are already in place.

## 0.3.2

AKA "just this one extra little thing".

* Added a fat32.FAT32._cluster_address() method (0.3.2).
* Added partition tables (MBR and GPT) write suport (0.3.2).
* Added (basic) VHD support (0.3.1)
* Added GPT parsing.
* Added utils module for general classes/functions.
* Added fat32.FAT32.open() method. (0.2.3)
* Small fixes to prevent unexpected behavior.
* Fixes a .seek() bug in FileHandle where it wasn't working for multi-clustered
  files (0.2.2). And then fixed it again, since it wasn't working for
  single-clustered files (0.2.3).
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