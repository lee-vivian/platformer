import utils
from solver import Solver
from run_solver import get_prolog_file_info, get_tile_ids_dictionary

import os

LEVELS = ['mario-1-1', 'mario-1-2', 'mario-1-3']
MAX_SOL = 5
PROLOG_CONFIG_FORMAT_PAIRS = [
    ("level_saved_files_block/prolog_files/%s.pl", "solver_config/widths_num_tiles/config-%s-50_num_tiles.json"),
    ("level_saved_files_block/prolog_files/%s.pl", "solver_config/widths_num_tiles/config-%s-100_num_tiles.json"),
    ("level_saved_files_block/prolog_files/%s.pl", "solver_config/widths_num_tiles/config-%s-150_num_tiles.json")
]
PLAYER_IMG = 'block'
CHECK_ASP_PATH = True
CHECK_STATE_GRAPH_PATH = False

model_str_file_format = "level_saved_files_block/generated_level_model_strs/%s.txt"
assignments_dict_file_format = "level_saved_files_block/generated_level_assignments_dicts/%s.pickle"


def main(levels, max_sol, prolog_config_format_pairs):

    # Create (prolog_file, config_file, level, sol) tuples
    solver_runs = []
    for prolog_format, config_format in prolog_config_format_pairs:
        for level in levels:
            for sol in range(max_sol):
                solver_runs.append((prolog_format % level, config_format % level, level, sol))

    # Initialize counts
    asp_checked_count = 0
    asp_valid_count = 0
    state_graph_checked_count = 0
    state_graph_valid_count = 0

    # Validate each tuple
    for prolog_file, config_file, level, sol in solver_runs:
        prolog_filename = utils.get_basepath_filename(prolog_file, 'pl')
        config_filename = utils.get_basepath_filename(config_file, 'json')
        answer_set_filename = '_'.join([prolog_filename, config_filename, 'a%d' % sol])

        if CHECK_ASP_PATH:

            prolog_file_info = get_prolog_file_info(prolog_file)
            tile_ids = get_tile_ids_dictionary(prolog_file_info)
            model_str_file = model_str_file_format % answer_set_filename

            if os.path.exists(model_str_file):

                model_str = utils.read_txt(model_str_file)
                asp_valid = Solver.asp_is_valid(check_path=True,
                                                check_onground=False if level == 'mario-1-2' else True,
                                                check_bonus=True,
                                                model_str=model_str,
                                                player_img=PLAYER_IMG,
                                                answer_set_filename=answer_set_filename,
                                                tile_ids=tile_ids,
                                                save=False)
                status = "ASP VALID" if asp_valid else "ASP INVALID"
                print("%s: %s" % (answer_set_filename, status))
                asp_checked_count += 1
                asp_valid_count += 1 if asp_valid else 0

        if CHECK_STATE_GRAPH_PATH:
            assignments_dict_file = assignments_dict_file_format % answer_set_filename
            if os.path.exists(assignments_dict_file):
                assignments_dict = utils.read_pickle(assignments_dict_file)
                state_graph_valid_path = Solver.get_state_graph_valid_path(assignments_dict, PLAYER_IMG, prolog_filename,
                                                                           answer_set_filename, save=False)
                status = "GRAPH VALID" if state_graph_valid_path else "GRAPH INVALID"
                print("%s: %s" % (answer_set_filename, status))
                state_graph_checked_count += 1
                state_graph_valid_count += 1 if state_graph_valid_path is not None else 0

    if CHECK_ASP_PATH:
        print("ASPs Checked: %d" % asp_checked_count)
        print("ASPs Valid: %d" % asp_valid_count)

    if CHECK_STATE_GRAPH_PATH:
        print("State Graphs Checked: %d" % state_graph_checked_count)
        print("State Graphs Valid: %d" % state_graph_valid_count)


if __name__ == "__main__":
    main(levels=LEVELS, max_sol=MAX_SOL, prolog_config_format_pairs=PROLOG_CONFIG_FORMAT_PAIRS)
