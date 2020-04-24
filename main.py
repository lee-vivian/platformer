"""
A. Process a level [use pypy3 interpreter]
B. Play a level [use python3 interpreter]
"""

import os
import argparse

import utils

ENVIRONMENTS = ['maze', 'platformer']


def main(environment, game, level, player_img, use_graph, draw_all_labels, draw_dup_labels, draw_path, show_score,
         process, solve, dimensions):

    # Set environment variable
    if environment not in ENVIRONMENTS:
        utils.error_exit("invalid environment - environment must be one of %s" % str(ENVIRONMENTS))
    if environment == 'maze':
        os.environ['MAZE'] = "1"

    if dimensions:
        from model.level import Level
        print(Level.get_level_dimensions_in_tiles(game, level))
        exit(0)

    if solve and not process:
        utils.error_exit("missing --process flag in command; required to run --solve")

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
        metatile_constraints_file = extract_constraints.main(save_filename=level, metatile_id_map_file=metatile_id_map_file,
                                                             id_metatile_map_file=id_metatile_map_file,
                                                             metatile_coords_dict_files=[metatile_coords_dict_file],
                                                             player_img=player_img)

        import gen_prolog
        prolog_file = gen_prolog.main(tile_constraints_file=metatile_constraints_file, debug=False, print_pl=False)

        if solve:
            from model.level import Level
            import run_solver
            level_w, level_h = Level.get_level_dimensions_in_tiles(game, level)
            run_solver.main(prolog_file=prolog_file, level_w =level_w, level_h=level_h, min_perc_blocks=None,
                            level_sections=1, max_sol=0, print_level_stats=False, save=True, validate=True)

    else:
        import platformer
        platformer.main(game, level, player_img, use_graph, draw_all_labels, draw_dup_labels, draw_path, show_score)


if __name__ == "__main__":

    # # --- FILE FORMATS ---
    # # Need player_img, game, and level
    # state_graph_file_format = "level_saved_files_%s/enumerated_state_graphs/%s/%s.gpickle"
    # metatile_coords_dict_file_format = "level_saved_files_%s/metatile_coords_dicts/%s/%s.pickle"
    #
    # # Need player img and level
    # unique_metatiles_file_format = "level_saved_files_%s/unique_metatiles/%s.pickle"
    # id_metatile_map_file_format = "level_saved_files_%s/id_metatile_maps/%s.pickle"
    # metatile_id_map_file_format = "level_saved_files_%s/metatile_id_maps/%s.pickle"
    #
    # # --- IMPORT STATEMENTS ---
    # from model.metatile import Metatile
    # import extract_metatiles  # individual and mario-all levels
    # import get_metatile_id_map  # individual and mario-all levels
    # import get_tile_id_coords_map  # individual levels
    #
    # # --- ADJUST VARIABLES ---
    # player_img = 'block'
    # GAME_LEVEL_PAIRS = [
    #     ('super_mario_bros', 'mario-1-1'), ('super_mario_bros', 'mario-2-1'), ('super_mario_bros', 'mario-3-1'),
    #     ('super_mario_bros', 'mario-3-2'), ('super_mario_bros', 'mario-4-1'), ('super_mario_bros', 'mario-5-1'),
    #     ('super_mario_bros', 'mario-5-2'), ('super_mario_bros', 'mario-6-1'), ('super_mario_bros', 'mario-6-2'),
    #     ('super_mario_bros', 'mario-7-1'), ('super_mario_bros', 'mario-8-1'), ('super_mario_bros', 'mario-8-2'),
    #     ('super_mario_bros', 'mario-8-3')
    # ]
    # combined_filename = 'mario-icarus-1'
    # RUN_INDIVIDUAL = False
    # RUN_COMBINED = False
    # CHECK_GAMES_IN_COMBINED = False
    #
    # # --- INDIVIDUAL LEVEL SCRIPTS --- (extract_metatiles, get_metatile_id_map, get_tile_id_coords_map)
    # if RUN_INDIVIDUAL:
    #     for game, level in GAME_LEVEL_PAIRS:
    #         state_graph_file = state_graph_file_format % (player_img, game, level)
    #
    #         unique_metatiles_file, metatile_coords_dict_file = extract_metatiles.main(save_filename=level,
    #                                                                                   player_img=player_img,
    #                                                                                   print_stats=False,
    #                                                                                   state_graph_files=[state_graph_file])
    #
    #         id_metatile_map_file, metatile_id_map_file = get_metatile_id_map.main(save_filename=level,
    #                                                                               unique_metatiles_file=unique_metatiles_file,
    #                                                                               player_img=player_img)
    #
    #         get_tile_id_coords_map.main(game=game, level=level, metatile_coords_dict_file=metatile_coords_dict_file,
    #                                     metatile_id_map_file=metatile_id_map_file, player_img=player_img)
    #
    # # --- COMBINED LEVEL SCRIPTS --- (extract_metatiles, get_metatile_id_map)
    # if RUN_COMBINED:
    #     state_graph_files = []
    #     for game, level in GAME_LEVEL_PAIRS:
    #         state_graph_file = state_graph_file_format % (player_img, game, level)
    #         state_graph_files.append(state_graph_file)
    #
    #     unique_metatiles_file, metatile_coords_dict_file = extract_metatiles.main(save_filename=combined_filename,
    #                                                                               player_img=player_img,
    #                                                                               print_stats=False,
    #                                                                               state_graph_files=state_graph_files)
    #     get_metatile_id_map.main(save_filename=combined_filename, unique_metatiles_file=unique_metatiles_file,
    #                              player_img=player_img)
    #
    # # --- GET GAMES FROM COMBINED METATILES ---
    # if CHECK_GAMES_IN_COMBINED:
    #     id_metatile_map = utils.read_pickle(id_metatile_map_file_format % (player_img, combined_filename))
    #     mario_only_tile_count = 0
    #     icarus_only_tile_count = 0
    #     both_tile_count = 0
    #
    #     for id, metatile_str in id_metatile_map.items():
    #         metatile = Metatile.from_str(metatile_str)
    #         games = metatile.get_games()
    #         if len(games) == 1:
    #             if 'super_mario_bros' in games:
    #                 mario_only_tile_count += 1
    #             elif 'kid_icarus' in games:
    #                 icarus_only_tile_count += 1
    #         else:
    #             if 'super_mario_bros' in games and 'kid_icarus' in games:
    #                 both_tile_count += 1
    #
    #     print("Mario-only tiles: %d" % mario_only_tile_count)
    #     print("Icarus-only tiles: %d" % icarus_only_tile_count)
    #     print("Both games tiles: %d" % both_tile_count)
    #     print("Sum: %d" % (mario_only_tile_count + icarus_only_tile_count + both_tile_count))
    #     print("Total tiles: %d" % len(id_metatile_map))
    #
    # exit(0)

    parser = argparse.ArgumentParser(description='Process or play a level')
    parser.add_argument('environment', type=str, help='platformer or maze')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--use_graph', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--draw_all_labels', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--draw_dup_labels', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--draw_path', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--show_score', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--process', const=True, nargs='?', type=bool, help="Run process scripts", default=False)
    parser.add_argument('--solve', const=True, nargs='?', type=bool, help="Run solver", default=False)
    parser.add_argument('--dimensions',const=True, nargs='?', type=bool, help="Get level dimensions in tiles (width, height)", default=False)

    args = parser.parse_args()

    main(args.environment, args.game, args.level, args.player_img,
         args.use_graph, args.draw_all_labels, args.draw_dup_labels, args.draw_path, args.show_score,
         args.process, args.solve, args.dimensions)
