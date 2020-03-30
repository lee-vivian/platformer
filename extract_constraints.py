'''
Generates a json file representing a tileset and the constraints for each tile's 8 neighbor positions
'''

import argparse
import os
import datetime

from model.level import Level, TILE_DIM
from model.metatile import Metatile, TYPE_IMG_MAP
import utils

TILE_TOP_LEFT = "0,0"

LEFT = "-1,0"
RIGHT = "1,0"
TOP = "0,-1"
BOTTOM = "0,1"
TOP_LEFT = "-1,-1"
BOTTOM_LEFT = "-1,1"
TOP_RIGHT = "1,-1"
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
            neighbor_coords[BOTTOM_LEFT] = Metatile.from_str(coord_metatile_str_dict.get((coord[0] - TILE_DIM, coord[1] + TILE_DIM)))
    if has_right:
        neighbor_coords[RIGHT] = Metatile.from_str(coord_metatile_str_dict.get((coord[0] + TILE_DIM, coord[1])))
        if has_top:
            neighbor_coords[TOP_RIGHT] = Metatile.from_str(coord_metatile_str_dict.get((coord[0] + TILE_DIM, coord[1] - TILE_DIM)))
        if has_bottom:
            neighbor_coords[BOTTOM_RIGHT] = Metatile.from_str(coord_metatile_str_dict.get((coord[0] + TILE_DIM, coord[1] + TILE_DIM)))

    return neighbor_coords


def get_tileset_dict(metatile_id_file, game, level, player_img):

    tiles_dict = {}

    # Get level dimensions in px
    level_w, level_h = (TILE_DIM * dim for dim in Level.get_level_dimensions_in_tiles(game, level))

    # Load metatile id map
    metatile_id_map = utils.read_pickle(metatile_id_file)

    # Get {metatile_str: metatile} dict
    unique_metatiles = Metatile.get_unique_metatiles_for_level(game, level, player_img)
    metatile_str_metatile_dict = {}
    for metatile in unique_metatiles:
        metatile_str_metatile_dict[metatile.to_str()] = metatile

    # Get {coord: metatile_str} dictionary for current level
    coord_metatile_dict_file = "level_saved_files_%s/coord_metatile_dicts/%s/%s.pickle" % (player_img, game, level)
    coord_metatile_str_dict = utils.read_pickle(coord_metatile_dict_file)

    count = 0
    total = len(coord_metatile_str_dict)
    first_quarter = int(0.25 * total)
    second_quarter = int(0.50 * total)
    third_quarter = int(0.75 * total)
    print("total num coords:", total)

    for coord in coord_metatile_str_dict.keys():

        count += 1
        if count == first_quarter:
            print("25% complete...")
        elif count == second_quarter:
            print("50% complete...")
        elif count == third_quarter:
            print("75% complete...")

        cur_metatile = Metatile.from_str(coord_metatile_str_dict[coord])
        cur_metatile_neighbors_dict = get_neighbor_metatiles_dict(coord, coord_metatile_str_dict, level_w, level_h)

        # Get standardized string

        # Get standardized string of cur_metatile and neighbor metatiles
        std_metatile_strs_to_find = [("CURRENT", cur_metatile)]
        std_metatile_strs_to_find += [(pos, metatile) for pos, metatile in cur_metatile_neighbors_dict.items()]

        # Get {pos: standardized_metatile_str} dict
        pos_std_metatile_str_dict = {}

        while len(std_metatile_strs_to_find) > 0:
            std_metatile_strs_to_find_copy = std_metatile_strs_to_find.copy()
            for pos, metatile in std_metatile_strs_to_find:
                for std_metatile_str, std_metatile in metatile_str_metatile_dict.items():
                    if metatile == std_metatile:
                        pos_std_metatile_str_dict[pos] = std_metatile_str
                        std_metatile_strs_to_find_copy.remove((pos, metatile))
                        break

            std_metatile_strs_to_find = std_metatile_strs_to_find_copy

        cur_metatile_str = pos_std_metatile_str_dict.get("CURRENT")
        del pos_std_metatile_str_dict['CURRENT']

        cur_metatile_id = metatile_id_map[cur_metatile_str]

        # Update adjacent neighbors for cur_metatile

        if tiles_dict.get(cur_metatile_id) is None:

            tmp_metatile = Metatile.from_str(cur_metatile_str)
            path = "tiles/platformer/%s" % TYPE_IMG_MAP[tmp_metatile.type]

            tiles_dict[cur_metatile_id] = {
                "path": path,
                "pos": TILE_TOP_LEFT,
                "type": tmp_metatile.type,
                "graph": str(tmp_metatile.graph_as_dict),
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


def main(metatile_id_file, games, levels, player_img, load_saved_files, outfile):

    metatile_constraints_dir = utils.get_save_directory("metatile_constraints", player_img)
    game_level_pairs = zip(games, levels)

    start_time = datetime.datetime.now()
    print("\nExtracting combined metatile constraints for: " + str(levels))

    combined_tileset_dict = {"tileSize": "%d,%d" % (TILE_DIM, TILE_DIM),
                             "tiles": {}}

    for game, level in game_level_pairs:

        level_tileset_constraints_file = metatile_constraints_dir + level + ".json"
        if load_saved_files and os.path.exists(level_tileset_constraints_file):
            print("Loading tileset constraints from:", level_tileset_constraints_file)
            level_tileset_dict = utils.read_json(level_tileset_constraints_file).get("tileset")
        else:
            print("Constructing tileset constraints for level %s ..." % level)
            level_tileset_dict = get_tileset_dict(metatile_id_file, game, level, player_img)

        combined_tileset_dict = merge_tileset_dicts(combined_tileset_dict, level_tileset_dict)

    output_tileset = {"tileset": combined_tileset_dict}

    end_time = datetime.datetime.now()
    print("Runtime:", str(end_time - start_time))

    if outfile is None:
        outfile = '_'.join(levels)
    outfile_path = metatile_constraints_dir + outfile + ".json"

    return utils.write_json(outfile_path, output_tileset)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Extract combined tileset constraints json for the specified levels')
    parser.add_argument('metatile_id_file', type=str, help='Filepath for metatile_id map')
    parser.add_argument('--games', type=str, nargs="+", help='List of games', default="")
    parser.add_argument('--levels', type=str, nargs="+", help='List of game levels', default="")
    parser.add_argument('--player_img', type=str, help="Player image", default='block')
    parser.add_argument('--load_saved_files', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--outfile', type=str, help="Output filename", default=None)
    args = parser.parse_args()

    main(args.metatile_id_file, args.games, args.levels, args.player_img, args.load_saved_files, args.outfile)
