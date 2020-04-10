"""
A. Process a level [use pypy3 interpreter]
B. Play a level [use python3 interpreter]
"""

import os
import argparse

import utils

ENVIRONMENTS = ['maze', 'platformer']


def main(environment, game, level, player_img, use_graph, draw_all_labels, draw_dup_labels, draw_path, process):

    # Set environment variable
    if environment not in ENVIRONMENTS:
        utils.error_exit("invalid environment - environment must be one of %s" % str(ENVIRONMENTS))
    if environment == 'maze':
        os.environ['MAZE'] = "1"

    if process:
        import enumerate
        state_graph_file = enumerate.main(game, level, player_img)

        import extract_metatiles
        unique_metatiles_file, metatile_coords_dict_file = extract_metatiles.main(save_filename=level,
                                                                                  player_img=player_img,
                                                                                  print_stats=False,
                                                                                  state_graph_files=[state_graph_file])

        import get_metatile_id_map
        id_metatile_map_file, metatile_id_map_file = get_metatile_id_map.main(save_filename=level,
                                                                              unique_metatiles_file=unique_metatiles_file,
                                                                              player_img=player_img)

        import get_tile_id_coords_map
        get_tile_id_coords_map.main(game, level, metatile_coords_dict_file, metatile_id_map_file, player_img)

        import get_states_per_metatile
        get_states_per_metatile.main(save_filename=level, unique_metatiles_file=unique_metatiles_file,
                                     player_img=player_img, print_stats=False)

        import extract_constraints
        extract_constraints.main(save_filename=level, metatile_id_map_file=metatile_id_map_file, id_metatile_map_file=id_metatile_map_file,
                                 metatile_coords_dict_files=[metatile_coords_dict_file], player_img=player_img)

    else:
        import platformer
        platformer.main(game, level, player_img, use_graph, draw_all_labels, draw_dup_labels, draw_path)


if __name__ == "__main__":

    # GAME_LEVEL_PAIRS = [
    #     ('super_mario_bros', 'mario-1-1'), ('super_mario_bros', 'mario-2-1'), ('super_mario_bros', 'mario-3-1'),
    #     ('super_mario_bros', 'mario-3-2'), ('super_mario_bros', 'mario-4-1'), ('super_mario_bros', 'mario-5-1'),
    #     ('super_mario_bros', 'mario-5-2'), ('super_mario_bros', 'mario-6-1'), ('super_mario_bros', 'mario-6-2'),
    #     ('super_mario_bros', 'mario-7-1'), ('super_mario_bros', 'mario-8-1'), ('super_mario_bros', 'mario-8-2'),
    #     ('super_mario_bros', 'mario-8-3')
    # ]

    parser = argparse.ArgumentParser(description='Process or play a level')
    parser.add_argument('environment', type=str, help='platformer or maze')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--use_graph', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--draw_all_labels', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--draw_dup_labels', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--draw_path', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--process', const=True, nargs='?', type=bool, help="Run process scripts", default=False)

    args = parser.parse_args()

    main(args.environment, args.game, args.level, args.player_img,
         args.use_graph, args.draw_all_labels, args.draw_dup_labels, args.draw_path, args.process)
