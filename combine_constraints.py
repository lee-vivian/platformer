"""
Get combined tile constraints file for the given levels
"""
import argparse
from datetime import datetime

import extract_metatiles
import get_metatile_id_map
import extract_constraints


def main(save_filename, games, levels, player_img):

    print("Creating combined tile constraints file for the given levels: %s ..." % str(levels))
    start_time = datetime.now()

    # Save file formats
    state_graph_file_format = "level_saved_files_%s/enumerated_state_graphs/%s/%s.gpickle"
    metatile_coords_dict_file_format = "level_saved_files_%s/metatile_coords_dicts/%s/%s.pickle"
    state_graph_files = []
    metatile_coords_dict_files = []

    # Get state_graph and metatile_coord_dict files for each level
    game_level_pairs = zip(games, levels)
    for game, level in game_level_pairs:
        state_graph_files.append(state_graph_file_format % (player_img, game, level))
        metatile_coords_dict_files.append(metatile_coords_dict_file_format % (player_img, game, level))

    # Get unique metatiles for the combined levels
    unique_metatiles_file, metatile_coords_dict_file = extract_metatiles.main(save_filename=save_filename,
                                                                              player_img=player_img, print_stats=False,
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

    end_time = datetime.now()
    print("Total Runtime: %s" % str(end_time-start_time))

    return combined_constraints_file


if __name__ == "__main__":

    # GAME_LEVEL_PAIRS = [
    #     ('super_mario_bros', 'mario-1-1'), ('super_mario_bros', 'mario-2-1'), ('super_mario_bros', 'mario-3-1'),
    #     ('super_mario_bros', 'mario-3-2'), ('super_mario_bros', 'mario-4-1'), ('super_mario_bros', 'mario-5-1'),
    #     ('super_mario_bros', 'mario-5-2'), ('super_mario_bros', 'mario-6-1'), ('super_mario_bros', 'mario-6-2'),
    #     ('super_mario_bros', 'mario-7-1'), ('super_mario_bros', 'mario-8-1'), ('super_mario_bros', 'mario-8-2'),
    #     ('super_mario_bros', 'mario-8-3')
    # ]
    # GAMES = [item[0] for item in GAME_LEVEL_PAIRS]
    # LEVELS = [item[1] for item in GAME_LEVEL_PAIRS]
    #
    # main(save_filename='mario-all', games=GAMES, levels=LEVELS, player_img='block')
    # exit(0)

    parser = argparse.ArgumentParser(description='Get combined tile constraints file for the given levels')
    parser.add_argument('save_filename', type=str, help='File name to save combined tile constraints to')
    parser.add_argument('--games', type=str, nargs='+')
    parser.add_argument('--levels', type=str, nargs='+')
    parser.add_argument('--player_img', type=str, help="Player image", default='block')
    args = parser.parse_args()

    main(args.save_filename, args.games, args.levels, args.player_img)
