import os
import argparse

from model.level import Level
import utils

GAME = "super_mario_bros"
LEVELS = ["mario-1-1", "mario-1-2", "mario-1-3"]
WIDTHS = [50, 100, 150]
CONFIG_SUFFIXES = []  # prefix = config-level, suffix = config specifications
MAX_SOL = 2
THREADS = 12

# # ----- CREATE CONFIG FILE -----

def create_config_file(config_suffix, game, level, perc_width=100, perc_height=100, start_within=10, goal_within=10,
                       reachable_platforms=True, reachable_bonus_tiles=True,
                       perc_tile_deviation=5, perc_tile_types=None):

    training_width, training_height = Level.get_level_dimensions_in_tiles(game, level)
    config_width = int(training_width * perc_width/100)
    config_height = int(training_height * perc_height/100)

    training_perc_tiles_map = Level.get_perc_tiles_map(game, level)

    perc_tile_ranges = {}

    if perc_tile_types is not None:
        for tile_type in perc_tile_types:
            training_perc = training_perc_tiles_map[tile_type]
            min_perc = max(training_perc - perc_tile_deviation, 0)
            max_perc = min(training_perc + perc_tile_deviation, 100)
            perc_tile_ranges[tile_type] = str((min_perc, max_perc))

    config = {
        "level_dimensions": {
            "width": config_width,
            "height": config_height
        },
        "tile_position_ranges": {
            "start_column": "(None, %d)" % (0 + (start_within - 1)),
            "goal_column": "(%d, None)" % (config_width - (goal_within - 1))
        },
        "require_all_platforms_reachable": str(reachable_platforms),
        "require_all_bonus_tiles_reachable": str(reachable_bonus_tiles)
    }

    if len(perc_tile_ranges) > 0:
        config['perc_tile_ranges'] = {}
        for tile_type, range_str in perc_tile_ranges.items():
            config['perc_tile_ranges'][tile_type] = range_str

    config_file = "solver_config/config-%s-%s.json" % (level, config_suffix)
    utils.write_json(config_file, {"config": config})




def main(process, solve):

    if process:
        print("----- PROCESSING -----")
        process_dir = utils.get_directory("process_console_output")

        for level in LEVELS:
            process_file = utils.get_filepath(process_dir, "%s.txt" % level)
            os.system("(time pypy3 main.py platformer super_mario_bros %s --process) > %s 2>&1" % (level, process_file))
            print("Saved to: %s" % process_file)

    if solve:
        print("----- SOLVING -----")
        solve_dir = utils.get_directory("solver_console_output")

        for level in LEVELS:
            prolog_file = "level_saved_files_block/prolog_files/%s.pl" % level
            solve_level_dir = utils.get_directory("%s/%s" % (solve_dir, level))

            for config_suffix in CONFIG_SUFFIXES:
                config_file = "solver_config/%s-%s.json" % (level, config_suffix)
                solve_file = utils.get_filepath(solve_level_dir, "%s.txt" % config_suffix)

                os.system("(time python run_solver.py %s %s --max_sol %d --threads %d --save --validate) > %s 2>&1" % (
                    prolog_file, config_file, MAX_SOL, THREADS, solve_file
                ))
                print("Saved to: %s" % solve_file)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Make system calls to process and run solver for specified levels')
    parser.add_argument('--process', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--solve', const=True, nargs='?', type=bool, default=False)
    args = parser.parse_args()
    main(process=args.process, solve=args.solve)

    # CREATE CONFIG FILES
    for width in WIDTHS:
        create_config_file(config_suffix="%d_blocks" % width, game="super_mario_bros", level="mario-1-1", perc_width=width,
                           perc_tile_types=['block'])
    exit(0)
