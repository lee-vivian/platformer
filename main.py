"""
A. Process a level [use pypy3 interpreter]
B. Play a level [use python3 interpreter]
"""

import os
import argparse

from model.level import Level
import utils

ENVIRONMENTS = ['maze', 'platformer']


def save_process_runtimes(process_key, process_runtimes):
    all_levels_process_info_file = utils.get_filepath("", "all_levels_process_info.pickle")
    if os.path.exists(all_levels_process_info_file):
        all_levels_process_info = utils.read_pickle(all_levels_process_info_file)
    else:
        all_levels_process_info = {}

    if all_levels_process_info.get(process_key) is None:
        all_levels_process_info[process_key] = {}

    for process_step, runtime_str in process_runtimes:
        all_levels_process_info[process_key][process_step] = runtime_str

    utils.write_pickle(all_levels_process_info_file, all_levels_process_info)


def main(environment, game, level, player_img, use_graph, draw_all_labels, draw_dup_labels, draw_path, show_score,
         draw_reachable, draw_unreachable, draw_training_labels, draw_enum_reachable,
         process, gen_prolog, dimensions, structure, summary, runtime, prolog):

    # Set environment variable
    if environment not in ENVIRONMENTS:
        utils.error_exit("invalid environment - environment must be one of %s" % str(ENVIRONMENTS))
    if environment == 'maze':
        os.environ['MAZE'] = "1"

    if dimensions or structure or summary:
        if dimensions:
            print(Level.get_level_dimensions_in_tiles(game, level))
        if structure:
            Level.print_structural_txt(game, level)
        if summary:
            Level.print_tile_summary(game, level)
            Level.print_start_goal_tile_locations(game, level)
            print("Num gaps: %d" % Level.get_num_gaps(game, level))
        exit(0)

    if runtime:
        import json

        all_levels_process_info_file = utils.get_filepath("", "all_levels_process_info.pickle")
        if not os.path.exists(all_levels_process_info_file):
            utils.error_exit("%s file not found" % all_levels_process_info_file)
        all_levels_process_info = utils.read_pickle(all_levels_process_info_file)

        cur_game_level = "%s/%s" % (game, level)

        for process_key, process_runtimes in all_levels_process_info.items():
            if process_key == cur_game_level:
                print("----- Process Script Runtimes -----")
                print("Game: %s" % game)
                print("Level: %s" % level)
                print(json.dumps(process_runtimes, indent=2))
                exit(0)

        utils.error_exit("Run 'pypy3 main.py <environment> %s %s --process'" % (game, level))

    if prolog:
        import json

        all_prolog_info_file = utils.get_filepath("level_saved_files_block/prolog_files", "all_prolog_info.pickle")
        if not os.path.exists(all_prolog_info_file):
            utils.error_exit("%s file not found" % all_prolog_info_file)
        all_prolog_info = utils.read_pickle(all_prolog_info_file)

        prolog_exists = all_prolog_info.get(level)
        if prolog_exists:
            print("----- Prolog Info -----")
            print("Game: %s" % game)
            print("Level: %s" % level)
            for key, item in prolog_exists.items():
                print("%s: %s" % (key, str(item)))
            exit(0)

        utils.error_exit("Run 'python main.py <environment> %s %s --gen_prolog'" % (game, level))

    if process:
        print("----- Creating Uniform Txt Layer File -----")
        Level.get_uniform_tile_chars(game, level)

        print("---- Processing Level -----")
        print("Game: %s" % game)
        print("Level: %s" % level)

        process_runtimes = []

        import enumerate
        state_graph_file, runtime = enumerate.main(game, level, player_img)
        process_runtimes.append(('enumerate', runtime))

        import extract_metatiles
        unique_metatiles_file, metatile_coords_dict_file, runtime = extract_metatiles.main(save_filename=level,
                                                                                           player_img=player_img,
                                                                                           print_stats=False,
                                                                                           state_graph_files=[state_graph_file])
        process_runtimes.append(('extract_metatiles', runtime))

        import get_metatile_id_map
        id_metatile_map_file, metatile_id_map_file, runtime = get_metatile_id_map.main(save_filename=level,
                                                                                       unique_metatiles_file=unique_metatiles_file,
                                                                                       player_img=player_img)
        process_runtimes.append(('get_metatile_id_map', runtime))

        import get_tile_id_coords_map
        tile_id_extra_info_coords_map_file, runtime = get_tile_id_coords_map.main(game, level, metatile_coords_dict_file,
                                                                                  metatile_id_map_file, player_img)
        process_runtimes.append(('get_tile_id_coords_map', runtime))

        import get_states_per_metatile
        runtime = get_states_per_metatile.main(save_filename=level, unique_metatiles_file=unique_metatiles_file,
                                               player_img=player_img, print_stats=False)
        process_runtimes.append(('get_states_per_metatile', runtime))

        import extract_constraints
        metatile_constraints_file, runtime = extract_constraints.main(save_filename=level,
                                                                      metatile_id_map_file=metatile_id_map_file,
                                                                      id_metatile_map_file=id_metatile_map_file,
                                                                      metatile_coords_dict_files=[metatile_coords_dict_file],
                                                                      player_img=player_img)
        process_runtimes.append(('extract_constraints', runtime))

        save_process_runtimes(process_key="%s/%s" % (game, level), process_runtimes=process_runtimes)

    if gen_prolog:
        import gen_prolog
        metatile_constraints_file = "level_saved_files_%s/metatile_constraints/%s.pickle" % (player_img, level)
        if not os.path.exists(metatile_constraints_file):
            utils.error_exit("%s file does not exist. Run 'pypy3 main.py %s %s %s --process' first" %
                             (metatile_constraints_file, environment, game, level))
        prolog_file, runtime = gen_prolog.main(tile_constraints_file=metatile_constraints_file, debug=False, print_pl=False, save=True)
        save_process_runtimes(process_key="%s/%s" % (game, level), process_runtimes=[('gen_prolog', runtime)])

    if not (process or gen_prolog):
        import platformer
        platformer.main(game, level, player_img, use_graph, draw_all_labels, draw_dup_labels, draw_path, show_score,
                        draw_reachable, draw_unreachable, draw_training_labels, draw_enum_reachable)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process or play a level')
    parser.add_argument('environment', type=str, help='platformer or maze')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--use_graph', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--draw_all_labels', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--draw_dup_labels', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--draw_path', const=True, nargs='?', type=bool, default=False, help="Filepath of solver model str solution for generated level")
    parser.add_argument('--show_score', const=True, nargs='?', type=bool, default=False, help="Filepath of solver model str solution for generated level")
    parser.add_argument('--draw_reachable', type=str, default=None)
    parser.add_argument('--draw_unreachable', type=str, default=None)
    parser.add_argument('--draw_training_labels', type=str, default=None)
    parser.add_argument('--draw_enum_reachable', const=True, nargs='?', type=bool, help="Draw reachable states from enumerated state graph", default=False)
    parser.add_argument('--process', const=True, nargs='?', type=bool, help="Run process scripts", default=False)
    parser.add_argument('--gen_prolog', const=True, nargs='?', type=bool, help="Generate prolog rules", default=False)
    parser.add_argument('--dimensions', const=True, nargs='?', type=bool, help="Get level dimensions in tiles (width, height)", default=False)
    parser.add_argument('--structure', const=True, nargs='?', type=bool, help="Print level txt structural layer", default=False)
    parser.add_argument('--summary', const=True, nargs='?', type=bool, help="Print level tile summmary stats", default=False)
    parser.add_argument('--runtime', const=True, nargs='?', type=bool, help="Print process script runtimes", default=False)
    parser.add_argument('--prolog', const=True, nargs='?', type=bool, help="Print prolog dictionary info for level", default=False)
    args = parser.parse_args()

    main(args.environment, args.game, args.level, args.player_img,
         args.use_graph, args.draw_all_labels, args.draw_dup_labels, args.draw_path, args.show_score,
         args.draw_reachable, args.draw_unreachable, args.draw_training_labels, args.draw_enum_reachable,
         args.process, args.gen_prolog, args.dimensions, args.structure, args.summary, args.runtime, args.prolog)
