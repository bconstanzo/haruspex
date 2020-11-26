"""
Basic VHD format support to test making a full, fixed size, working VHD file
from scratch.

References:
https://github.com/libyal/libvhdi/blob/master/documentation/Virtual%20Hard%20Disk%20(VHD)%20image%20format.asciidoc
https://www.forensicfocus.com/articles/virtual-hard-disk-image-format-a-forensic-overview/
"""
import datetime
import struct


from .guid import GUID


class VHDFooter:
    """
    VHD Fixed Disk Footer to be found at the end of a VHD file (raw image + 
    VHD Header).
    """

    vhd_disk_types = {
        0: "None",
        1: "Reserved (deprecated) #1",
        2: "Fixed hard disk",
        3: "Dynamic hard disk",
        4: "Differential hard disk",
        5: "Reserved (deprecated) #5",
        6: "Reserved (deprecated) #6",
    }

    def __init__(self, data):
        """
        :param data: the 512 bytes that make the VHD Fixed Footer
        """
        self._raw_data = data
        # only the first 85 bytes have information, the rest is/should be \x00
        cook, feat, form, nxto = struct.unpack(">8sLLq",   data[  : 24])
        mtim, capp, cver, chos = struct.unpack(">L4sL4s",  data[24: 40])
        disz, dasz, dgeo, dtyp = struct.unpack(">QQ4sL",   data[40: 64])
        csum, guid, stat       = struct.unpack(">l16sB",   data[64: 85])
        # and now a few transformations before we set it all into the attributes
        mtim = datetime.datetime(2000, 1, 1) + datetime.timedelta(0, mtim)
        cver_major = cver >> 16
        cver_minor = cver & 0x0000ffff
        cver = (cver_major, cver_minor)
        cyl, head, sec = struct.unpack(">HBB", dgeo)
        dgeo = (cyl, head, sec)
        # and now we set the _ attributes for the properties
        self._cookie            = cook 
        self._features          = feat
        self._format_version    = form
        self._next_offset       = nxto
        self._modification_time = mtim
        self._creator_app       = capp
        self._creator_version   = cver
        self._creator_host      = chos
        self._disk_size         = disz
        self._data_size         = dasz
        self._disk_geometry     = dgeo
        self._disk_type         = dtyp
        self._checksum          = csum
        self._identifier        = GUID(guid)
        self._saved_state       = stat
    
    def __bytes__(self):
        data = bytearray()
        # a few of the properties need some preprocessing before being packed
        # as bytes
        modtime = self._modification_time - datetime.datetime(2000, 1, 1)
        modtime = (modtime.days * 86400) + modtime.seconds
        cver_major, cver_minor = self._creator_version
        cver = (cver_major << 16) | cver_minor
        cyl, head, sec = self._disk_geometry
        dgeo = struct.pack(">HBB", cyl, head, sec)
        # ok, now we're ready to pack!
        data += struct.pack(
            ">8sLLqL4sL4sQQ4sLl16sB",
            self._cookie,
            self._features,
            self._format_version,
            self._next_offset,  
            modtime,
            self._creator_app,
            cver,
            self._creator_host, 
            self._disk_size,    
            self._data_size,       
            dgeo,
            self._disk_type,   
            0,                     # checksum, we calculate it on the spot
            bytes(self._identifier),
            self._saved_state
        )
        checksum = ~sum(data)
        data[64:68] = struct.pack(">l", checksum)
        data += bytes(427)
        return bytes(data)

    @property
    def cookie(self):
        """Cookie. Read only, fixed as b"conectix"."""
        return self._cookie
    
    @cookie.setter
    def cookie(self, value):
        pass

    @property
    def features(self):
        """Features. Read only, fixed as 2."""
        return self._features
    
    @features.setter
    def features(self, value):
        pass

    @property
    def format_version(self):
        """Format version. Read only, fixed as 0x00010000."""
        return self._format_version
    
    @format_version.setter
    def format_version(self, value):
        pass

    @property
    def next_offset(self):
        """Next offset. Read only, fixed as -1."""
        return self._next_offset
    
    @next_offset.setter
    def next_offset(self, value):
        pass

    @property
    def modification_time(self):
        """
        Modification time. Second resolution. Can't store datetimes before 
        2000-01-01.
        """
        return self._modification_time
    
    @modification_time.setter
    def modification_time(self, value):
        value = datetime.datetime.replace(value, microsecond=0)
        if value < datetime.datetime(2000, 1, 1):
            value = datetime.datetime(2000, 1, 1)
        self._modification_time = value

    @property
    def creator_app(self):
        """
        Creator application. Gets encoded as bytes with "ascii" encoding, and
        capped at 4 bytes long.
        """
        return self._creator_app
    
    @creator_app.setter
    def creator_app(self, value):
        if isinstance(value, str):
            value = value.encode("ascii")
        if len(value) < 4:
            value += b"\x20" * (4 - len(value))  # extend with spaces
        self._creator_app = value
    
    @property
    def creator_version(self):
        """
        Creator version. Tuple of ints, get encoded as 2 16-bit values glued
        together into a 32-bit int.
        """
        return self._creator_version
    
    @creator_version.setter
    def creator_version(self, value):
        major, minor = value
        major, minor = int(major), int(minor)  # just making sure
        if major > 0xffff:
            major = 0xffff
        if minor > 0xffff:
            minor = 0xffff
        self._creator_version = (major, minor)
    
    @property
    def creator_host(self):
        """
        Creator host. Gets encoded as bytes with "ascii" encoding, and capped at
        4 bytes long.
        """
        return self._creator_host
    
    @creator_host.setter
    def creator_host(self, value):
        if isinstance(value, str):
            value = value.encode("ascii")
        if len(value) < 4:
            value += b"\x20" * (4 - len(value))  # extend with spaces
        value = value[0:4]
        self._creator_host = value

    @property
    def disk_size(self):
        """Disk size. 64-bit int."""
        return self._disk_size
    
    @disk_size.setter
    def disk_size(self, value):
        value = int(value)  #   just making sure...
        value = max(value, 0)
        value = min(value, 0xffffffffffffffff)
        self._disk_size = value
    
    @property
    def data_size(self):
        """Data size. 64-bit int."""
        return self._data_size
    
    @data_size.setter
    def data_size(self, value):
        value = int(value)  #   just making sure...
        value = max(value, 0)
        value = min(value, 0xffffffffffffffff)  # and a bit of clipping
        self._data_size = value
    
    @property
    def disk_geometry(self):
        """Disk geometry in as a (cylinder, head, sector) tuple of ints."""
        return self._disk_geometry
    
    @disk_geometry.setter
    def disk_geometry(self, value):
        cylinder, head, sector = map(int, value)
        cylinder = min(max(cylinder, 0), 65535)
        head     = min(max(head,   0), 255)
        sector   = min(max(sector, 0), 255)
        # maybe throw an error on these cases? shouldn't happen, but still
        self._disk_geometry = (cylinder, head, sector)
    
    @property
    def disk_type(self):
        """
        Disk type. See VHDFooter.vhd_disk_types for valid values.
        """
        k = self._disk_type
        v = self.vhd_disk_types.get(k, "Unknown")
        return v
    
    @disk_type.setter
    def disk_type(self, value):
        value = int(value)
        if 0 <= value <= 6:
            raise ValueError("the given value is not in the 0..6 range")
        self._disk_type = value
    
    @property
    def checksum(self):
        """
        Checksum. Read-only, gets recalculated on conversion of footer to bytes.
        """
        return self._checksum

    @checksum.setter
    def checksum(self, value):
        pass

    @property
    def identifier(self):
        """Identifier GUID."""
        return self._identifier
    
    @identifier.setter
    def identifier(self, value):
        if not(isinstance(value, GUID)):
            raise ValueError(f"expected GUID, got {type(identifier)} instead")
        self._identifier = value
    
    @property
    def saved_state(self):
        """
        Saved state. Flag to indicate the image is in saved staty. 8-bit int.
        """
        return self._saved_state
    
    @saved_state.setter
    def saved_state(self, value):
        value = int(value)
        value = min(max(value, 0), 255)
        self._saved_state = value
    
    def __repr__(self):
        r = (f"< VHDFooter: {self.disk_type}"
             f"{self.disk_size} (last modified {self.modification_time})>"
            )
        return r
    
    def __str__(self):
        ret = [
            f"< VHDFooter @ {id(self)} >",
            f"           cookie: {str(self.cookie):>20}",
            f"         features: {str(self.features):>20}",
            f"   format version: {str(self.format_version):>20}",
            f"      next offset: {str(self.next_offset):>20}",
            f"modification time: {str(self.modification_time):>20}",
            f"      creator app: {str(self.creator_app):>20}",
            f"  creator version: {str(self.creator_version):>20}",
            f"     creator host: {str(self.creator_host):>20}",
            f"        disk size: {str(self.disk_size):>20}",
            f"        data size: {str(self.data_size):>20}",
            f"    disk geometry: {str(self.disk_geometry):>20}",
            f"        disk type: {str(self.disk_type):>20}",
            f"         checksum: {str(self.checksum):>20}",
            f"       identifier: {str(self.identifier):>20}",
            f"      saved state: {str(self.saved_state):>20}",
        ]
        return "\n".join(ret)
