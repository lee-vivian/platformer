'''
Generates a json file representing a tileset and the constraints for each tile's 8 neighbor positions
'''

import os
import json
import datetime

from model.level import Level
from model.metatile import Metatile

PLAYER_IMG = 'block'
TILE_IMG = "tiles/platformer/tile.png"
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


def get_metatile_constraints_dir():
    level_saved_files_dir = "level_saved_files_" + PLAYER_IMG + "/"
    metatile_constraints_dir = level_saved_files_dir + "metatile_constraints/"
    saved_files_directories = [level_saved_files_dir, metatile_constraints_dir]

    for directory in saved_files_directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

    return metatile_constraints_dir


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


def get_tileset_dict(game_name, level_name):

    print("Constructing tileset for level %s ..." % level_name)

    tiles_dict = {}

    # Generate level from txt file
    level = Level.generate_level_from_file(game_name + "/" + level_name + ".txt")

    # Get {metatile_str: metatile} dict
    unique_metatiles = Metatile.get_unique_metatiles_for_level(game_name, level_name, PLAYER_IMG)
    metatile_str_metatile_dict = {}
    for metatile in unique_metatiles:
        metatile_str_metatile_dict[metatile.to_str()] = metatile

    # Get {coord: metatile_str} dictionary for current level
    coord_metatile_dict_file = "level_saved_files_%s/coord_metatile_dicts/%s/%s.txt" % (PLAYER_IMG, game_name, level_name)
    f = open(coord_metatile_dict_file, 'r')
    coord_metatile_str_dict = eval(f.readline())
    f.close()

    all_possible_coords = level.get_all_possible_coords()
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
        cur_metatile_neighbors_dict = get_neighbor_metatiles_dict(metatile_coord, coord_metatile_str_dict, level.width, level.height)

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

        # Update adjacent neighbors for cur_metatile

        if tiles_dict.get(cur_metatile_str) is None:
            tiles_dict[cur_metatile_str] = {
                "path": TILE_IMG,
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

        adjacent_neighbors_dict = tiles_dict.get(cur_metatile_str).get("adjacent").copy()
        for pos, metatile_str in pos_std_metatile_str_dict.items():
            if metatile_str not in adjacent_neighbors_dict.get(pos):
                adjacent_neighbors_dict[pos].append(metatile_str)

        tiles_dict[cur_metatile_str]['adjacent'] = adjacent_neighbors_dict

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


def save_tileset_to_json(metatile_constraints_dir, subdir, tileset_dict, constraint_filename):

    directory_to_save_file = metatile_constraints_dir + subdir + "/"
    if not os.path.exists(directory_to_save_file):
        os.makedirs(directory_to_save_file)

    metatile_constraints_str = json.dumps({"tileset": tileset_dict}, indent=2)
    metatile_constraints_filepath = directory_to_save_file + str(constraint_filename) + ".json"
    with open(metatile_constraints_filepath, 'w') as f:
        f.write(metatile_constraints_str)
    f.close()
    print("Saved to:", metatile_constraints_filepath)


def main(game_level_pairs, combine_levels_tile_constraints, combined_constraints_filename):

    metatile_constraints_dir = get_metatile_constraints_dir()

    if not combine_levels_tile_constraints:
        for game, level in game_level_pairs:
            print("Extracting metatile constraints for %s ..." % level)
            start_time = datetime.datetime.now()

            tileset_dict = get_tileset_dict(game, level)
            save_tileset_to_json(metatile_constraints_dir, game, tileset_dict, constraint_filename=level)

            end_time = datetime.datetime.now()
            print("Runtime:", str(end_time-start_time))

    else:
        games, levels = map(list, zip(*game_level_pairs))

        if combined_constraints_filename is None:
            combined_constraints_filename = str(levels)

        print("Extracting combined metatile constraints for: " + str(levels))
        start_time = datetime.datetime.now()

        combined_tileset_dict = {"tileSize": "%d,%d" % (TILE_DIM, TILE_DIM),
                                 "tiles": {}}

        for game, level in game_level_pairs:
            # Check if tileset for individual level already exists
            level_tileset_filepath = metatile_constraints_dir + game + "/" + level + ".json"
            if os.path.exists(level_tileset_filepath):
                print("Loading tileset from:", level_tileset_filepath)
                with open(level_tileset_filepath) as file:
                    level_tileset_dict = json.load(file)["tileset"]
                file.close()
            else:
                level_tileset_dict = get_tileset_dict(game, level)

            combined_tileset_dict = merge_tileset_dicts(combined_tileset_dict, level_tileset_dict)

        save_tileset_to_json(metatile_constraints_dir, "combined_levels", combined_tileset_dict, constraint_filename=combined_constraints_filename)

        end_time = datetime.datetime.now()
        print("Runtime:", str(end_time-start_time))


if __name__ == "__main__":

    COMBINED_CONSTRAINTS_FILENAME = "all_levels"  # specify name of combined constraint file
    COMBINE_LEVEL_TILE_CONSTRAINTS = False  # if False, generate individual tile constraint file for each level
    GAME_LEVEL_PAIRS = [
        ('sample', 'sample_hallway'),
        ('super_mario_bros', 'mario-1-1'),
        ('super_mario_bros', 'mario-2-1'),
        ('kid_icarus', 'kidicarus_1')
    ]

    COMBINED_CONSTRAINTS_FILENAME = None if not COMBINE_LEVEL_TILE_CONSTRAINTS else COMBINED_CONSTRAINTS_FILENAME

    main(GAME_LEVEL_PAIRS, COMBINE_LEVEL_TILE_CONSTRAINTS, COMBINED_CONSTRAINTS_FILENAME)

