"""
Generates a pickle file representing a tileset and the constraints for each tile's 8 neighbor positions
"""

import argparse
from datetime import datetime

from model.level import TILE_DIM
from model.metatile import Metatile
from utils import read_pickle, write_pickle, get_filepath

LEFT = (-1, 0)
RIGHT = (1, 0)
TOP = (0, -1)
BOTTOM = (0, 1)
TOP_LEFT = (-1, -1)
BOTTOM_LEFT = (-1, 1)
TOP_RIGHT = (1, -1)
BOTTOM_RIGHT = (1, 1)
DIRECTIONS = [LEFT, RIGHT, TOP, BOTTOM, TOP_LEFT, BOTTOM_LEFT, TOP_RIGHT, BOTTOM_RIGHT]

# # [ ] [T] [ ]
# # [L] [X] [R]
# # [ ] [B] [ ]


def get_coord_metatiles_dict(metatile_coords_dicts):
    # Get all metatiles at each coord
    coord_metatiles_dict_tmp = {}
    for metatile_coord_dict in metatile_coords_dicts:
        for metatile_str, coords in metatile_coord_dict.items():
            metatile = Metatile.from_str(metatile_str)
            for coord in coords:
                if coord_metatiles_dict_tmp.get(coord) is None:
                    coord_metatiles_dict_tmp[coord] = []
                coord_metatiles_dict_tmp[coord].append(metatile)

    # Remove duplicate metatiles
    coord_metatiles_dict = {}
    for coord, metatiles in coord_metatiles_dict_tmp.items():
        coord_metatiles_dict[coord] = Metatile.get_unique_metatiles(metatiles)
    
    return coord_metatiles_dict


def get_coord_tile_ids_map(metatile_id_map, coord_metatiles_dict):
    ordered_metatiles = []
    ordered_ids = []
    for metatile_str, id in metatile_id_map.items():
        ordered_metatiles.append(Metatile.from_str(metatile_str))
        ordered_ids.append(id)

    coord_tile_ids_map = {}
    for coord, metatiles in coord_metatiles_dict.items():
        coord_tile_ids_map[coord] = []
        for metatile in metatiles:
            tile_id_idx = ordered_metatiles.index(metatile)
            tile_id = ordered_ids[tile_id_idx]
            coord_tile_ids_map[coord].append(tile_id)

    return coord_tile_ids_map


def populate_tile_id_constraints_adjacencies(tile_id_constraints_dict, coord_tile_ids_map):

    def get_direction_neighbor_coord_map(coord):
        cur_map = {}
        for direction in DIRECTIONS:
            neighbor_x = coord[0] + (direction[0] * TILE_DIM)
            neighbor_y = coord[1] + (direction[1] * TILE_DIM)
            cur_map[direction] = (neighbor_x, neighbor_y)
        return cur_map  # {DIRECTION: neighbor_coord}

    coord_tile_ids_map_copy = coord_tile_ids_map.copy()  # clone for reference

    for coord, tile_ids in coord_tile_ids_map.items():
        direction_neighbor_coord_map = get_direction_neighbor_coord_map(coord)

        for direction, neighbor_coord in direction_neighbor_coord_map.items():
            neighbor_tile_ids = coord_tile_ids_map_copy.get(neighbor_coord)  # get tile_ids at neighbor coord
            if neighbor_tile_ids is not None and len(neighbor_tile_ids) > 0:

                for id in tile_ids:  # update adjacent tiles in the cur direction for every tile_id at the current coord
                    tile_adjacency_direction_dict = tile_id_constraints_dict[id]['adjacent'][direction]
                    tile_adjacency_direction_dict = list(set(tile_adjacency_direction_dict + neighbor_tile_ids))
                    tile_id_constraints_dict[id]['adjacent'][direction] = tile_adjacency_direction_dict

    return tile_id_constraints_dict


def main(save_filename, metatile_id_map_file, id_metatile_map_file, metatile_coords_dict_files, player_img):

    print("Constructing tile_id constraints dictionary...")
    start_time = datetime.now()

    # Create save file path
    metatile_constraints_dir = "level_saved_files_%s/metatile_constraints" % player_img
    metatile_constraints_file = get_filepath(metatile_constraints_dir, "%s.pickle" % save_filename)

    # Load in files
    metatile_id_map = read_pickle(metatile_id_map_file)
    id_metatile_map = read_pickle(id_metatile_map_file)
    metatile_coords_dicts = [read_pickle(file) for file in metatile_coords_dict_files]

    coord_metatiles_dict = get_coord_metatiles_dict(metatile_coords_dicts)
    coord_tile_ids_map = get_coord_tile_ids_map(metatile_id_map, coord_metatiles_dict)

    tile_id_constraints_dict = {}
    for tile_id, metatile_str in id_metatile_map.items():
        metatile = Metatile.from_str(metatile_str)
        tile_id_constraints_dict[tile_id] = {
            "type": metatile.type,
            "graph": metatile.graph_as_dict,
            "adjacent": {
                TOP: [], BOTTOM: [], LEFT: [], RIGHT: [], TOP_LEFT: [], BOTTOM_LEFT: [], TOP_RIGHT: [], BOTTOM_RIGHT: []
            }
        }
    tile_id_constraints_dict = populate_tile_id_constraints_adjacencies(tile_id_constraints_dict, coord_tile_ids_map)

    end_time = datetime.now()
    print("Runtime: %s" % str(end_time-start_time))

    write_pickle(metatile_constraints_file, tile_id_constraints_dict)
    return metatile_constraints_file


if __name__ == "__main__":

    # GAME_LEVEL_PAIRS = [
    #     ('super_mario_bros', 'mario-1-1'), ('super_mario_bros', 'mario-2-1'), ('super_mario_bros', 'mario-3-1'),
    #     ('super_mario_bros', 'mario-3-2'), ('super_mario_bros', 'mario-4-1'), ('super_mario_bros', 'mario-5-1'),
    #     ('super_mario_bros', 'mario-5-2'), ('super_mario_bros', 'mario-6-1'), ('super_mario_bros', 'mario-6-2'),
    #     ('super_mario_bros', 'mario-7-1'), ('super_mario_bros', 'mario-8-1'), ('super_mario_bros', 'mario-8-2'),
    #     ('super_mario_bros', 'mario-8-3'), ('kid_icarus', 'kidicarus_1')
    # ]
    #
    # metatile_id_map_file_format = "level_saved_files_block/metatile_id_maps/%s.pickle"
    # id_metatile_map_file_format = "level_saved_files_block/id_metatile_maps/%s.pickle"
    # metatile_coords_dict_file_format = "level_saved_files_block/metatile_coords_dicts/%s/%s.pickle"
    #
    # # For individual level constraints
    # for game, level in GAME_LEVEL_PAIRS:
    #     main(save_filename=level,
    #          metatile_id_map_file=metatile_id_map_file_format % level,
    #          id_metatile_map_file=id_metatile_map_file_format % level,
    #          metatile_coords_dict_files=[metatile_coords_dict_file_format % (game, level)],
    #          player_img='block')
    #
    # combined = 'combined_levels'
    # metatile_coords_dict_files = []
    # for game, level in GAME_LEVEL_PAIRS:
    #     file = "level_saved_files_block/metatile_coords_dicts/%s/%s.pickle" % (game, level)
    #     metatile_coords_dict_files.append(file)
    # main(combined, metatile_id_map_file_format % combined, id_metatile_map_file_format % combined,
    #      metatile_coords_dict_files, player_img='block')
    #
    # exit(0)

    parser = argparse.ArgumentParser(description='Extract combined tileset constraints for the specified levels')
    parser.add_argument('save_filename', type=str, help='File name to save tileset constraints to')
    parser.add_argument('metatile_id_map_file', type=str, help='Filepath for metatile_id map')
    parser.add_argument('id_metatile_map_file', type=str, help='Filepath for id_metatile map')
    parser.add_argument('metatile_coords_dict_files', type=str, nargs="+", help="Filepath to metatile_coord_dict files to use")
    parser.add_argument('--player_img', type=str, help="Player image", default='block')
    args = parser.parse_args()

    main(args.save_filename, args.metatile_id_map_file, args.id_metatile_map_file, args.metatile_coords_dict_files,
         args.player_img)

