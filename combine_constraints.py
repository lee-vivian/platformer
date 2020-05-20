"""
Get combined tile constraints file for the given levels
"""
import argparse
import os

import extract_metatiles
import get_metatile_id_map
import extract_constraints
import gen_prolog
from utils import error_exit


def main(game_levels, save_filename, player_img):

    print("Creating combined tile constraints file for the given levels: %s ..." % str(game_levels))

    # Saved filename formats
    state_graph_file_format = "level_saved_files_%s/enumerated_state_graphs/%s/%s.gpickle"
    metatile_coords_dict_file_format = "level_saved_files_%s/metatile_coords_dicts/%s/%s.pickle"
    state_graph_files = []
    metatile_coords_dict_files = []
    level_names = []

    # Get state graph and metatile_coord_dict files for each level
    for game_level in game_levels:
        game, level = game_level.split('/')
        state_graph_file = state_graph_file_format % (player_img, game, level)
        metatile_coords_dict_file = metatile_coords_dict_file_format % (player_img, game, level)

        if not os.path.exists(state_graph_file):
            error_exit("Missing state graph for %s." % level)
        else:
            state_graph_files.append(state_graph_file)

        if not os.path.exists(metatile_coords_dict_file):
            error_exit("Missing metatile_coords_dict_file for %s." % level)
        else:
            metatile_coords_dict_files.append(metatile_coords_dict_file)

        level_names.append(level)

    save_filename = "_".join(level_names) if save_filename is None else save_filename

    # Get unique metatiles for the combined levels
    unique_metatiles_file, metatile_coords_dict_file = extract_metatiles.main(save_filename=save_filename,
                                                                              player_img=player_img,
                                                                              print_stats=False,
                                                                              state_graph_files=state_graph_files)

    # Get id_metatile and metatile_id maps for the combined levels
    id_metatile_map_file, metatile_id_map_file = get_metatile_id_map.main(save_filename=save_filename,
                                                                          unique_metatiles_file=unique_metatiles_file,
                                                                          player_img=player_img)

    # Get combined tile constraints map for the combined levels
    combined_constraints_file = extract_constraints.main(save_filename=save_filename,
                                                         metatile_id_map_file=metatile_id_map_file,
                                                         id_metatile_map_file=id_metatile_map_file,
                                                         metatile_coords_dict_files=metatile_coords_dict_files,
                                                         player_img=player_img)

    # Generate prolog file for the combined level constraints
    prolog_file = gen_prolog.main(tile_constraints_file=combined_constraints_file, debug=False, print_pl=False)

    return prolog_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get combined tile constraints file for the given levels')
    parser.add_argument('game_levels', type=str, nargs='+', help='List of game/level')
    parser.add_argument('--save_filename', type=str, help='File name to save combined tile constraints to', default=None)
    parser.add_argument('--player_img', type=str, help="Player image", default='block')
    args = parser.parse_args()

    main(args.game_levels, args.save_filename, args.player_img)
