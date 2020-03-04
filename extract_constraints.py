'''
Generates a json file representing a tileset and the constraints for each tile's 8 neighbor positions
'''

import os
import json

from model.level import Level
from model.metatile import Metatile

PLAYER_IMG = 'block'
TILE_IMG = "images/tile.png"
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


def get_tiles_dict(game_name, level_name, player_img):

    tiles_dict = {}

    # Generate level from txt file
    level = Level.generate_level_from_file(game_name + "/" + level_name + ".txt")

    # Get {metatile_str: metatile} dict
    unique_metatiles = Metatile.get_unique_metatiles_for_level(level_name, player_img)
    metatile_str_metatile_dict = {}
    for metatile in unique_metatiles:
        metatile_str_metatile_dict[metatile.to_str()] = metatile

    # Get {coord: metatile_str} dictionary for current level
    coord_metatile_dict_file = "level_saved_files_%s/coord_metatile_dicts/%s.txt" % (player_img, level_name)
    f = open(coord_metatile_dict_file, 'r')
    coord_metatile_str_dict = eval(f.readline())
    f.close()

    for metatile_coord in level.get_all_possible_coords():

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
            adjacent_neighbors_dict[pos] += metatile_str

        tiles_dict[cur_metatile_str]['adjacent'] = adjacent_neighbors_dict

    return tiles_dict


def get_tileset(game, level):

    tileset_dict = {"tileSize": "%d,%d" % (TILE_DIM, TILE_DIM),
                    "tiles": get_tiles_dict(game, level, PLAYER_IMG)}

    level_saved_files_dir = "level_saved_files_" + PLAYER_IMG + "/"
    metatile_constraints_dir = level_saved_files_dir + "metatile_constraints/"
    saved_files_directories = [level_saved_files_dir, metatile_constraints_dir]

    for directory in saved_files_directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

    metatile_constraints_file = metatile_constraints_dir + str(level) + ".json"
    with open(metatile_constraints_file, 'w') as file:
        json.dump(tileset_dict, file, indent=2, sort_keys=True)

    print(str(tileset_dict))
    return tileset_dict


