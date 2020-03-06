'''
Creates and saves a map of {metatile-id: Metatile} for a given list of metatiles
'''

import argparse
import os
import pickle

from model.metatile import Metatile


def error_message(msg):
    print(msg)
    exit(0)


def get_metatile_id_map_dir(player_img):
    metatile_id_map_dir = "level_saved_files_%s/metatile_id_maps/" % player_img
    if not os.path.exists(metatile_id_map_dir):
        os.makedirs(metatile_id_map_dir)
    return metatile_id_map_dir


def main(games, levels, player_img, outfile):

    if len(games) != len(levels):
        error_message("Given number of games must equal then number of levels")
    elif len(levels) == 0:
        error_message("No levels specified")

    metatile_id_map = {}
    metatile_count = 0
    game_level_pairs = zip(games, levels)
    metatiles = Metatile.get_unique_metatiles_for_levels(game_level_pairs, player_img)

    for metatile in metatiles:
        metatile_count += 1
        metatile_id = "t%d" % metatile_count
        metatile_id_map[metatile_id] = metatile.to_str()

    metatile_id_map_dir = get_metatile_id_map_dir(player_img)

    if outfile is None:
        outfile = '_'.join(levels)
    outfile_path = metatile_id_map_dir + outfile + ".pickle"

    with open(outfile_path, 'wb') as file:
        pickle.dump(metatile_id_map, file, protocol=pickle.HIGHEST_PROTOCOL)

    print("Saved to:", outfile_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get map of {metatile-id: Metatile} for the given game levels')
    parser.add_argument('--games', type=str, nargs="+", help='List of games', default="")
    parser.add_argument('--levels', type=str, nargs="+", help='List of game levels', default="")
    parser.add_argument('--player_img', type=str, help="Player image", default='block')
    parser.add_argument('--outfile', type=str, help="Output filename", default=None)
    args = parser.parse_args()

    main(args.games, args.levels, args.player_img, args.outfile)

