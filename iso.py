import gdf
from enum import IntEnum


class ISO:

    def __init__(self, iso_path):
        # Create ISO Object

        try:  # Try to open iso file
            self.file = open(iso_path, 'rb')
            self.gdf = gdf.GDF(self.file)
        except IOError as e:
            raise IOError(f"Could not open ISO file.\n{e}")


class ISOType(IntEnum):
    """The type of the ISO."""
    XSF = 0
    GDF = 265879552
    XGD3 = 34078720
