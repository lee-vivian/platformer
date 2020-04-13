"""
Creates and saves a map of {metatile-id: Metatile} for a given list of metatiles
"""

import argparse
import os
from datetime import datetime

from utils import read_pickle, write_pickle, get_filepath


def get_id_metatile_map_file(player_img, outfile):
    id_metatile_map_dir = "level_saved_files_%s/id_metatile_maps/" % player_img
    if not os.path.exists(id_metatile_map_dir):
        os.makedirs(id_metatile_map_dir)
    id_metatile_map_file = id_metatile_map_dir + outfile + ".pickle"
    return id_metatile_map_file


def get_metatile_id_map_file(player_img, outfile):
    metatile_id_map_dir = "level_saved_files_%s/metatile_id_maps/" % player_img
    if not os.path.exists(metatile_id_map_dir):
        os.makedirs(metatile_id_map_dir)
    metatile_id_map_file = metatile_id_map_dir + outfile + ".pickle"
    return metatile_id_map_file


def main(save_filename, unique_metatiles_file, player_img):

    print("Creating id maps from unique metatiles file %s..." % unique_metatiles_file)
    start_time = datetime.now()

    metatile_count = 0
    id_metatile_map = {}
    metatile_id_map = {}

    unique_metatiles = read_pickle(unique_metatiles_file)

    for metatile in unique_metatiles:
        metatile_count += 1
        metatile_id = "t%d" % metatile_count
        metatile_str = metatile.to_str()
        id_metatile_map[metatile_id] = metatile_str
        metatile_id_map[metatile_str] = metatile_id

    level_saved_files_dir = "level_saved_files_%s/" % player_img
    outfile = "%s.pickle" % save_filename

    id_metatile_map_file = get_filepath(level_saved_files_dir + "id_metatile_maps", outfile)
    metatile_id_map_file = get_filepath(level_saved_files_dir + "metatile_id_maps", outfile)

    write_pickle(id_metatile_map_file, id_metatile_map)
    write_pickle(metatile_id_map_file, metatile_id_map)

    end_time = datetime.now()
    print("Runtime: %s" % str(end_time-start_time))

    return id_metatile_map_file, metatile_id_map_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get metatile_id maps for the given unique_metatiles file')
    parser.add_argument('save_filename', type=str, help='File name to save extracted info to')
    parser.add_argument('unique_metatiles_file', type=str, help='File path of unique_metatiles file to use')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    args = parser.parse_args()

    main(args.save_filename, args.unique_metatiles_file, args.player_img)
