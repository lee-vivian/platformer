'''
Generates a json file representing a tileset and the constraints for each tile's 8 neighbor positions
'''

import argparse
import os
import datetime
import pickle
import json

from model.level import Level
from model.metatile import Metatile

TILE_IMG = "tiles/platformer/gray_tile.png"
BLANK_TILE_IMG = "tiles/platformer/blank_tile.png"
TILE_TOP_LEFT = "0,0"
TILE_DIM = 40

LEFT = "-1,0"
RIGHT = "1,0"
TOP = "0,-1"
BOTTOM = "0,1"
TOP_LEFT = "-1,-1"
TOP_RIGHT = "1,-1"
BOTTOM_LEFT = "-1,1"
BOTTOM_RIGHT = "1,1"


def get_metatile_constraints_dir(player_img):
    metatile_constraints_dir = "level_saved_files_%s/metatile_constraints/" % player_img
    if not os.path.exists(metatile_constraints_dir):
        os.makedirs(metatile_constraints_dir)
    return metatile_constraints_dir


def read_pickle(filepath):
    with open(filepath, 'rb') as file:
        contents = pickle.load(file)
    file.close()
    return contents


def write_pickle(filepath, contents):
    with open(filepath, 'wb') as file:
        pickle.dump(contents, file, protocol=pickle.HIGHEST_PROTOCOL)
    file.close()
    print("Saved to:", filepath)
    return filepath


def read_json(filepath):
    with open(filepath, 'r') as file:
        contents = json.load(file)
    file.close()
    return contents


def write_json(filepath, contents):
    with open(filepath, 'w') as file:
        json.dump(contents, file, indent=2, sort_keys=True)
    file.close()
    print("Saved to:", filepath)
    return filepath


# [ ] [ ] [ ]
# [ ] [X] [ ]
# [ ] [ ] [ ]

def get_neighbor_metatiles_dict(coord, coord_metatile_str_dict, level_width, level_height):
    neighbor_coords = {}

    has_top = coord[1] > 0
    has_bottom = coord[1] + TILE_DIM < level_height
    has_left = coord[0] > 0
    has_right = coord[0] + TILE_DIM < level_width

    if has_top:
        neighbor_coords[TOP] = Metatile.from_str(coord_metatile_str_dict.get((coord[0], coord[1] - TILE_DIM)))
    if has_bottom:
        neighbor_coords[BOTTOM] = Metatile.from_str(coord_metatile_str_dict.get((coord[0], coord[1] + TILE_DIM)))
    if has_left:
        neighbor_coords[LEFT] = Metatile.from_str(coord_metatile_str_dict.get((coord[0] - TILE_DIM, coord[1])))
        if has_top:
            neighbor_coords[TOP_LEFT] = Metatile.from_str(coord_metatile_str_dict.get((coord[0] - TILE_DIM, coord[1] - TILE_DIM)))
        if has_bottom:
            neighbor_coords[TOP_RIGHT] = Metatile.from_str(coord_metatile_str_dict.get((coord[0] - TILE_DIM, coord[1] + TILE_DIM)))
    if has_right:
        neighbor_coords[RIGHT] = Metatile.from_str(coord_metatile_str_dict.get((coord[0] + TILE_DIM, coord[1])))
        if has_top:
            neighbor_coords[TOP_RIGHT] = Metatile.from_str(coord_metatile_str_dict.get((coord[0] + TILE_DIM, coord[1] - TILE_DIM)))
        if has_bottom:
            neighbor_coords[BOTTOM_RIGHT] = Metatile.from_str(coord_metatile_str_dict.get((coord[0] + TILE_DIM, coord[1] + TILE_DIM)))

    return neighbor_coords


def get_tileset_dict(metatile_id_map, game, level, player_img):

    tiles_dict = {}

    # Generate Level from txt file
    level_obj = Level.generate_level_from_file("%s/%s.txt" % (game, level))

    # Get {metatile_str: metatile} dict
    unique_metatiles = Metatile.get_unique_metatiles_for_level(game, level, player_img)
    metatile_str_metatile_dict = {}
    for metatile in unique_metatiles:
        metatile_str_metatile_dict[metatile.to_str()] = metatile

    # Get {coord: metatile_str} dictionary for current level
    coord_metatile_dict_file = "level_saved_files_%s/coord_metatile_dicts/%s/%s.txt" % (player_img, game, level)
    f = open(coord_metatile_dict_file, 'r')
    coord_metatile_str_dict = eval(f.readline())
    f.close()

    all_possible_coords = level_obj.get_all_possible_coords()
    count = 0
    total = len(all_possible_coords)
    first_quarter = int(0.25 * total)
    second_quarter = int(0.50 * total)
    third_quarter = int(0.75 * total)

    print("total num coords:", total)

    for metatile_coord in all_possible_coords:

        count += 1
        if count == first_quarter:
            print("25% complete...")
        elif count == second_quarter:
            print("50% complete...")
        elif count == third_quarter:
            print("75% complete...")

        cur_metatile = Metatile.from_str(coord_metatile_str_dict.get(metatile_coord))
        cur_metatile_neighbors_dict = get_neighbor_metatiles_dict(metatile_coord, coord_metatile_str_dict,
                                                                  level_obj.width, level_obj.height)

        # Get standardized string of cur_metatile and neighbor metatiles
        std_metatile_strs_to_find = [("CURRENT", cur_metatile)]
        std_metatile_strs_to_find += [(pos, metatile) for pos, metatile in cur_metatile_neighbors_dict.items()]

        # Get {pos: standardized_metatile_str} dict
        pos_std_metatile_str_dict = {}

        while len(std_metatile_strs_to_find) > 0:
            std_metatile_strs_to_find_copy = std_metatile_strs_to_find.copy()

            for key, value in metatile_str_metatile_dict.items():
                for pos, metatile in std_metatile_strs_to_find:
                    if value == metatile:
                        pos_std_metatile_str_dict[pos] = key
                        std_metatile_strs_to_find_copy.remove((pos, metatile))
                        break

            std_metatile_strs_to_find = std_metatile_strs_to_find_copy

        cur_metatile_str = pos_std_metatile_str_dict.get("CURRENT")
        del pos_std_metatile_str_dict['CURRENT']

        cur_metatile_id = metatile_id_map[cur_metatile_str]

        # Update adjacent neighbors for cur_metatile

        if tiles_dict.get(cur_metatile_id) is None:

            tmp_metatile = Metatile.from_str(cur_metatile_str)
            graph_is_empty = not bool(tmp_metatile.graph_as_dict)
            path = TILE_IMG if graph_is_empty else BLANK_TILE_IMG

            tiles_dict[cur_metatile_id] = {
                "path": path,
                "pos": TILE_TOP_LEFT,
                "adjacent": {
                    TOP: [],
                    BOTTOM: [],
                    LEFT: [],
                    RIGHT: [],
                    TOP_LEFT: [],
                    BOTTOM_LEFT: [],
                    TOP_RIGHT: [],
                    BOTTOM_RIGHT: []
                }
            }

        adjacent_neighbors_dict = tiles_dict.get(cur_metatile_id).get("adjacent").copy()
        for pos, metatile_str in pos_std_metatile_str_dict.items():
            metatile_id = metatile_id_map[metatile_str]
            if metatile_id not in adjacent_neighbors_dict.get(pos):
                adjacent_neighbors_dict[pos].append(metatile_id)

        tiles_dict[cur_metatile_id]['adjacent'] = adjacent_neighbors_dict

    print("100% complete ...")

    tileset_dict = {"tileSize": "%d,%d" % (TILE_DIM, TILE_DIM),
                    "tiles": tiles_dict}

    return tileset_dict


def merge_tileset_dicts(combined_tileset_dict, level_tileset_dict):

    combined_tile_size = combined_tileset_dict.get("tileSize")
    combined_tiles_dict = combined_tileset_dict.get("tiles").copy()
    level_tiles_dict = level_tileset_dict.get("tiles")

    for tile_key, tile_value in level_tiles_dict.items():

        if combined_tiles_dict.get(tile_key) is None:  # tile not already in combined_tiles_dict
            combined_tiles_dict[tile_key] = tile_value

        else:
            combined_tile_neighbors_dict = combined_tiles_dict[tile_key]['adjacent']
            level_tile_neighbors_dict = tile_value['adjacent']

            for pos, neighbor_tiles in level_tile_neighbors_dict.items():
                if combined_tile_neighbors_dict.get(pos) is None:  # pos not seen for this tile yet
                    combined_tile_neighbors_dict[pos] = neighbor_tiles
                else:
                    combined_tile_neighbors_dict[pos] = \
                        list(set(combined_tile_neighbors_dict.get(pos) + neighbor_tiles))

    return {
        "tileSize": combined_tile_size,
        "tiles": combined_tiles_dict
    }


def main(metatile_id_file, games, levels, player_img, outfile):

    metatile_constraints_dir = get_metatile_constraints_dir(player_img)
    metatile_id_map = read_pickle(metatile_id_file)
    game_level_pairs = zip(games, levels)

    start_time = datetime.datetime.now()
    print("Extracting combined metatile constraints for: " + str(levels))

    combined_tileset_dict = {"tileSize": "%d,%d" % (TILE_DIM, TILE_DIM),
                             "tiles": {}}

    for game, level in game_level_pairs:
        level_tileset_file = metatile_constraints_dir + level + ".json"
        if os.path.exists(level_tileset_file):
            print("Loading tileset constrints from:", level_tileset_file)
            level_tileset_dict = read_json(level_tileset_file).get("tileset")
        else:
            print("Constructing tileset constraints for level %s ..." % level)
            level_tileset_dict = get_tileset_dict(metatile_id_map, game, level, player_img)

        combined_tileset_dict = merge_tileset_dicts(combined_tileset_dict, level_tileset_dict)

    output_tileset = {"tileset": combined_tileset_dict}

    end_time = datetime.datetime.now()
    print("Runtime:", str(end_time - start_time))

    if outfile is None:
        outfile = '_'.join(levels)
    outfile_path = metatile_constraints_dir + outfile + ".json"

    return write_json(outfile_path, output_tileset)


if __name__ == "__main__":

    # GAME_LEVEL_PAIRS = [
    #     ('sample', 'sample_hallway'),
    #     ('super_mario_bros', 'mario-1-1'),
    #     ('super_mario_bros', 'mario-2-1'),
    #     ('kid_icarus', 'kidicarus_1')
    # ]
    #
    # for game, level in GAME_LEVEL_PAIRS:
    #     main('level_saved_files_block/metatile_id_maps/%s.pickle' % level,
    #          [game], [level], 'block', None)

    parser = argparse.ArgumentParser(description='Extract combined tileset constraints json for the specified levels')
    parser.add_argument('metatile_id_file', type=str, help='Filepath for metatile_id map')
    parser.add_argument('--games', type=str, nargs="+", help='List of games', default="")
    parser.add_argument('--levels', type=str, nargs="+", help='List of game levels', default="")
    parser.add_argument('--player_img', type=str, help="Player image", default='block')
    parser.add_argument('--outfile', type=str, help="Output filename", default=None)
    args = parser.parse_args()

    main(args.metatile_id_file, args.games, args.levels, args.player_img, args.outfile)

#   pypy3 extract_constraints.py level_saved_files_block/metatile_id_maps/all_levels.pickle --games sample super_mario_bros super_mario_bros kid_icarus --levels sample_hallway mario-1-1 mario-2-1 kidicarus_1 --outfile all_levels


