import os
import argparse

import utils

GAME = "super_mario_bros"
# LEVELS = ["mario-sample"]
LEVELS = ["mario-1-1", "mario-1-2", "mario-1-3"]

PROLOG_CONFIG_FORMAT_PAIRS = [
    ("level_saved_files_block/prolog_files/%s.pl", "solver_config/widths_num_tiles/config-%s-50_num_tiles.json"),
    ("level_saved_files_block/prolog_files/%s.pl", "solver_config/widths_num_tiles/config-%s-100_num_tiles.json"),
    ("level_saved_files_block/prolog_files/%s.pl", "solver_config/widths_num_tiles/config-%s-150_num_tiles.json")
]


def main(process, solve, max_sol, threads):

    if process:
        print("----- PROCESSING -----")
        process_dir = utils.get_directory("process_console_output")

        for level in LEVELS:
            process_file = utils.get_filepath(process_dir, "%s.txt" % level)
            os.system("(time pypy3 main.py platformer %s %s --process) > %s 2>&1" % (GAME, level, process_file))
            print("Saved to: %s" % process_file)

    if solve:
        print("----- SOLVING -----")
        solve_dir = utils.get_directory("solver_console_output")

        level_prolog_config_tuples = []
        for prolog_format, config_format in PROLOG_CONFIG_FORMAT_PAIRS:
            for level in LEVELS:
                level_prolog_config_tuples.append((level, prolog_format % level, config_format % level))

        sol_order = list(range(max_sol))
        sol_order.reverse()

        for sol in sol_order:
            for level, prolog_file, config_file in level_prolog_config_tuples:
                prolog_filename = utils.get_basepath_filename(prolog_file, 'pl')
                config_filename = utils.get_basepath_filename(config_file, 'json')
                solve_file = utils.get_filepath("%s/%s/" % (solve_dir, level), "%s_a%d.txt" % (config_filename, sol))

                os.system("(time python run_solver.py %s %s --max_sol 1 --threads %d --save --validate) > %s 2>&1" % (
                    prolog_file, config_file, threads, solve_file
                ))
                print("Saved to: %s" % solve_file)

                answer_set_filename = "_".join([prolog_filename, config_filename, "a%d"])
                level_structural_txt_format = "level_structural_layers/generated/%s.txt" % answer_set_filename
                level_assignments_format = "level_saved_files_block/generated_level_assignments_dicts/%s.pickle" % answer_set_filename
                level_model_str_format = "level_saved_files_block/generated_level_model_strs/%s.txt" % answer_set_filename
                level_valid_path_format = "level_saved_files_block/generated_level_paths/%s.pickle" % answer_set_filename
                level_state_graph_format = "level_saved_files_block/enumerated_state_graphs/generated/%s.gpickle" % answer_set_filename

                if sol != 0 and os.path.exists(level_structural_txt_format % 0):
                    os.system("mv %s %s" % (level_structural_txt_format % 0, level_structural_txt_format % sol))

                if sol != 0 and os.path.exists(level_assignments_format % 0):
                    os.system("mv %s %s" % (level_assignments_format % 0, level_assignments_format % sol))

                if sol != 0 and os.path.exists(level_model_str_format % 0):
                    os.system("mv %s %s" % (level_model_str_format % 0, level_model_str_format % sol))

                if sol != 0 and os.path.exists(level_valid_path_format % 0):
                    os.system("mv %s %s" % (level_valid_path_format % 0, level_valid_path_format % sol))

                if sol != 0 and os.path.exists(level_state_graph_format % 0):
                    os.system("mv %s %s" % (level_state_graph_format % 0, level_state_graph_format % sol))

                if os.path.exists(level_structural_txt_format % sol):
                    print("Level txt path: %s" % level_structural_txt_format % sol)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Make system calls to process and run solver for specified levels')
    parser.add_argument('--process', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--solve', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--max_sol', type=int, default=1, help="Max number of answer sets to return per solver run")
    parser.add_argument('--threads', type=int, default=1, help="Number of threads to run the solver on")
    args = parser.parse_args()
    main(process=args.process, solve=args.solve, max_sol=args.max_sol, threads=args.threads)

