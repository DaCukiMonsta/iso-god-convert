from dataclasses import dataclass
from enum import IntEnum
import iso
import os


class GDF:

    magic_string = "MICROSOFT*XBOX*MEDIA"

    def __init__(self, iso_file_object):
        self.file = iso_file_object

        self.file.seek(0, os.SEEK_END)
        self.file_size = self.file.tell()

        self.__read_volume()
        self.root_dir = DirectoryTable(self)

    def __read_volume(self):
        self.volume_descriptor = VolumeDescriptor()
        self.volume_descriptor.sector_size = 2048

        self.type = None
        for this_type in iso.ISOType:
            self.file.seek((32 * self.volume_descriptor.sector_size) + this_type)
            try:
                if self.file.read(20).decode('ascii') == GDF.magic_string:
                    self.type = this_type
                    break
            except UnicodeDecodeError:
                pass  # It's okay, we just know this one isn't valid ascii

        if self.type is None:  # Check that we found the type
            raise NotImplementedError("Unknown ISO type. Is this definitely an Xbox/360 ISO?")

        self.volume_descriptor.root_offset = self.type
        self.volume_descriptor.identifier = self.magic_string  # we just checked this was equal, so we know what it is
        self.volume_descriptor.root_dir_sector = int.from_bytes(self.file.read(4), byteorder='little')
        self.volume_descriptor.root_dir_size = int.from_bytes(self.file.read(4), byteorder='little')
        self.volume_descriptor.image_creation_time = self.file.read(8)
        self.volume_descriptor.volume_size = self.file_size - self.volume_descriptor.root_offset
        self.volume_descriptor.volume_sectors = self.volume_descriptor.volume_size / \
            self.volume_descriptor.sector_size


@dataclass
class VolumeDescriptor:
    """Represents a GDF Volume Descriptor."""
    identifier: bytes = None
    root_dir_sector: int = None
    root_dir_size: int = None
    image_creation_time: bytes = None
    sector_size: int = None
    root_offset: int = None
    volume_size: int = None
    volume_sectors: int = None


class DirectoryEntryAttributes(IntEnum):
    """Attributes for a GDF directory entry."""
    ReadOnly = 1
    Hidden = 2
    System = 4
    Directory = 16
    Archive = 32
    Normal = 128


@dataclass
class DirectoryEntry:
    """Represents a GDF directory entry."""
    subtree_l: int = None
    subtree_r: int = None
    sector: int = None
    size: int = None
    attributes: DirectoryEntryAttributes = None
    name_length: int = None
    name: str = None
    padding: bytes = None
    subdir: 'DirectoryTable' = None  # why use single quotes here? see: https://github.com/python/typing/issues/34
    parent: 'DirectoryTable' = None


class DirectoryTable(list):

    def __init__(self, gdf=None, sector=None, size=None):
        super().__init__()
        self.gdf = gdf
        if gdf is None:
            self.size = 2048
            self.tree = AVLTree()
            return
        elif sector is None:
            self.sector = self.gdf.volume_descriptor.root_dir_sector
            self.size = self.gdf.volume_descriptor.root_dir_size

        base_position = self.sector * self.gdf.volume_descriptor.sector_size + self.gdf.volume_descriptor.root_offset
        self.gdf.file.seek(base_position)

        try:
            while self.gdf.file.tell() < base_position + self.size:
                dir_entry = DirectoryEntry()
                dir_entry.subtree_l = int.from_bytes(self.__safe_read(self.gdf.file, 2), byteorder='little')
                dir_entry.subtree_r = int.from_bytes(self.__safe_read(self.gdf.file, 2), byteorder='little')
                if dir_entry.subtree_l != 65535 and dir_entry.subtree_r != 65535:
                    dir_entry.sector = int.from_bytes(self.__safe_read(self.gdf.file, 4), byteorder='little')
                    dir_entry.size = int.from_bytes(self.__safe_read(self.gdf.file, 4), byteorder='little')
                    dir_entry.attributes = int.from_bytes(self.__safe_read(self.gdf.file, 1), byteorder='little')
                    dir_entry.name_length = int.from_bytes(self.__safe_read(self.gdf.file, 1), byteorder='little')
                    dir_entry.name = self.__safe_read(self.gdf.file, dir_entry.name_length).decode('ascii')

                    # seek to the next multiple of 4 bytes
                    if self.gdf.file.tell() % 4 > 0:
                        self.gdf.file.seek(4 - (self.gdf.file.tell() % 4), os.SEEK_CUR)
                    self.append(dir_entry)
        except EOFError as e:
            raise EOFError(f"Unexpectedly reached end of file when parsing GDF directory table.\n{e}")

    @staticmethod
    def __safe_read(file, size=-1):
        bytes_read = file.read(size)
        if size != -1 and len(bytes_read) < size:
            raise EOFError(f"{size} bytes were requested to be read, but only {len(bytes_read)} were read before "
                           f"an EOF.")
        return bytes_read


class AVLTree:

    def __init__(self):
        pass
