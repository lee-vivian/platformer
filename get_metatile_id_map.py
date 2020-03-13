'''
Creates and saves a map of {metatile-id: Metatile} for a given list of metatiles
'''

import argparse
import os

from model.metatile import Metatile
from utils import error_exit, write_pickle


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


def main(games, levels, player_img, outfile):

    print("\nGet metatile_id maps for levels: " + str(levels) + "...")

    if len(games) != len(levels):
        error_exit("Given number of games must equal the given number of levels")
    elif len(levels) == 0:
        error_exit("No levels specified")

    if outfile is None:
        outfile = '_'.join(levels)

    metatile_count = 0
    id_metatile_map = {}
    metatile_id_map = {}

    game_level_pairs = zip(games, levels)
    unique_metatiles = Metatile.get_unique_metatiles_for_levels(game_level_pairs, player_img)

    for metatile in unique_metatiles:
        metatile_count += 1
        metatile_id = "t%d" % metatile_count
        metatile_str = metatile.to_str()
        id_metatile_map[metatile_id] = metatile_str
        metatile_id_map[metatile_str] = metatile_id

    id_metatile_map_file = get_id_metatile_map_file(player_img, outfile)
    metatile_id_map_file = get_metatile_id_map_file(player_img, outfile)

    return write_pickle(id_metatile_map_file, id_metatile_map), write_pickle(metatile_id_map_file, metatile_id_map)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Get metatile_id maps for the given game levels')
    parser.add_argument('--games', type=str, nargs="+", help='List of games', default="")
    parser.add_argument('--levels', type=str, nargs="+", help='List of game levels', default="")
    parser.add_argument('--player_img', type=str, help="Player image", default='block')
    parser.add_argument('--outfile', type=str, help="Output filename", default=None)
    args = parser.parse_args()

    main(args.games, args.levels, args.player_img, args.outfile)

# pypy3 get_metatile_id_map.py --games sample sample sample super_mario_bros super_mario_bros kid_icarus --levels sample_mini sample_hallway_flat sample_hallway mario-1-1 mario-2-1 kidicarus_1 --outfile all_levels