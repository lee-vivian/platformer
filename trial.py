import os
import re
import argparse

import utils

GAME = "super_mario_bros"
LEVELS = ["mario-sample"]
# LEVELS = ["mario-1-1", "mario-1-2", "mario-1-3"]

PROLOG_CONFIG_PAIRS = [
    ("level_saved_files_block/prolog_files/%s.pl", "solver_config/widths/config-%s-50.json"),
    ("level_saved_files_block/prolog_files/%s.pl", "solver_config/widths/config-%s-100.json"),
    ("level_saved_files_block/prolog_files/%s.pl", "solver_config/widths/config-%s-150.json"),
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

        for level in LEVELS:
            solve_level_dir = utils.get_directory("%s/%s" % (solve_dir, level))

            for prolog_file, config_file in PROLOG_CONFIG_PAIRS:
                config_filename = os.path.basename(config_file % level)
                config_filename = re.match(r'([.a-zA-Z0-9_-]+).json', config_filename)
                config_filename = config_filename.group(1)
                solve_file = utils.get_filepath(solve_level_dir, "%s.txt" % config_filename)

                print("Solve file: %s" % solve_file)

                os.system("(time python run_solver.py %s %s --max_sol %d --threads %d --save --validate) > %s 2>&1" % (
                    prolog_file % level, config_file % level, max_sol, threads, solve_file
                ))

                print("Saved to: %s" % solve_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Make system calls to process and run solver for specified levels')
    parser.add_argument('--process', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--solve', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--max_sol', type=int, default=1, help="Max number of answer sets to return per solver run")
    parser.add_argument('--threads', type=int, default=1, help="Number of threads to run the solver on")
    args = parser.parse_args()
    main(process=args.process, solve=args.solve, max_sol=args.max_sol, threads=args.threads)

