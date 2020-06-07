from solver import Solver
from run_solver import get_prolog_file_info, get_tile_ids_dictionary
from trial import TRIAL_CONFIG_FORMATS
import utils

import os
import argparse


def main(trial, levels, num_sol, asp, state_graph):

    if not (asp or state_graph):
        utils.error_exit("Must specify at least one validation test to run: --asp or --state_graph")

    # Get file formats
    config_formats = TRIAL_CONFIG_FORMATS.get(trial)
    if config_formats is None:
        utils.error_exit("--trial must be one of %s" % str(list(TRIAL_CONFIG_FORMATS.keys())))
    prolog_file_format = "level_saved_files_block/prolog_files/%s.pl"
    model_str_file_format = "level_saved_files_block/generated_level_model_strs/%s.txt"
    assignments_dict_file_format = "level_saved_files_block/generated_level_assignments_dicts/%s.pickle"

    # Initialize validation counts
    asp_checked_count = 0
    asp_valid_count = 0
    state_graph_checked_count = 0
    state_graph_valid_count = 0

    # Validate each solver run
    for level in levels:
        for config_file_format in config_formats:
            for sol in range(num_sol):
                prolog_file = prolog_file_format % level
                prolog_filename = utils.get_basepath_filename(prolog_file, 'pl')
                config_file = config_file_format % level
                config_filename = utils.get_basepath_filename(config_file, 'json')
                answer_set_filename = '_'.join([prolog_filename, config_filename, 'a%d' % sol])

                if asp:
                    # Determine ASP checks to perform based on config file contents
                    config_file_contents = utils.read_json(config_file)
                    config = config_file_contents['config']
                    require_all_platforms_reachable = True
                    require_all_bonus_tiles_reachable = True
                    if config.get('require_all_platforms_reachable') is not None:
                        require_all_platforms_reachable = eval(config['require_all_platforms_reachable'])
                    if config.get('require_all_bonus_tiles_reachable') is not None:
                        require_all_bonus_tiles_reachable = eval(config['require_all_bonus_tiles_reachable'])

                    prolog_file_info = get_prolog_file_info(prolog_file)
                    tile_ids = get_tile_ids_dictionary(prolog_file_info)
                    model_str_file = model_str_file_format % answer_set_filename

                    if os.path.exists(model_str_file):
                        model_str = utils.read_txt(model_str_file)
                        asp_valid = Solver.asp_is_valid(check_path=True,
                                                        check_onground=require_all_platforms_reachable,
                                                        check_bonus=require_all_bonus_tiles_reachable,
                                                        model_str=model_str,
                                                        player_img='block',
                                                        answer_set_filename=answer_set_filename,
                                                        tile_ids=tile_ids,
                                                        save=False)
                        status = "ASP VALID" if asp_valid else "ASP INVALID"
                        print("%s: %s" % (answer_set_filename, status))
                        asp_checked_count += 1
                        asp_valid_count += 1 if asp_valid else 0

                if state_graph:
                    assignments_dict_file = assignments_dict_file_format % answer_set_filename
                    if os.path.exists(assignments_dict_file):
                        assignments_dict = utils.read_pickle(assignments_dict_file)
                        valid_path = Solver.get_state_graph_valid_path(assignments_dict=assignments_dict,
                                                                       player_img='block',
                                                                       prolog_filename=prolog_filename,
                                                                       answer_set_filename=answer_set_filename,
                                                                       save=True)
                        status = "GRAPH VALID" if valid_path else "GRAPH INVALID"
                        print("%s: %s" % (answer_set_filename, status))
                        state_graph_checked_count += 1
                        state_graph_valid_count += 1 if valid_path is not None else 0

    # Print validation results summary
    if asp:
        print("ASPs Checked: %d" % asp_checked_count)
        print("ASPs Valid: %d" % asp_valid_count)

    if state_graph:
        print("State Graphs Checked: %d" % state_graph_checked_count)
        print("State Graphs Valid: %d" % state_graph_valid_count)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Validate generated levels')
    parser.add_argument('trial', type=str, help="Trial to run: options %s" % str(list(TRIAL_CONFIG_FORMATS.keys())))
    parser.add_argument('levels', type=str, nargs='+', help="Level names")
    parser.add_argument('--num_sol', type=int, default=1, help="Number of answer sets per config to validate")
    parser.add_argument('--asp', const=True, nargs='?', type=bool, default=False, help="Validate generated level ASP model str")
    parser.add_argument('--state_graph', const=True, nargs='?', type=bool, default=False, help="Validate generated level state graph")
    args = parser.parse_args()
    main(trial=args.trial, levels=args.levels, num_sol=args.num_sol, asp=args.asp, state_graph=args.state_graph)

