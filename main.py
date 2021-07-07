from iso import *

if __name__ == '__main__':
    iso = ISO("test.iso")

    print("ISO Type:", iso.gdf.type)
    print("Root directory:")
    for entry in iso.gdf.root_dir:
        print('\t', entry.name)
