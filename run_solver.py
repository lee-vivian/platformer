import signal
import argparse

from solver import Solver
from utils import get_filepath, read_pickle

"""
Run clingo solver on the given prolog file with the specified params
"""


def keyboard_interrupt_handler(signal, frame, solver):
    print("----- KEYBOARD INTERRUPT -----")
    solver.end_and_validate()
    exit(0)


def main(prolog_file, level_w, level_h, min_perc_blocks, level_sections, max_sol, print_level_stats, save, validate):
    player_img, prolog_filename = Solver.parse_prolog_filepath(prolog_file)
    level_saved_files_dir = "level_saved_files_%s/" % player_img
    all_prolog_info_file = get_filepath(level_saved_files_dir + "prolog_files", "all_prolog_info.pickle")
    all_prolog_info_map = read_pickle(all_prolog_info_file)
    prolog_file_info = all_prolog_info_map.get(prolog_filename)

    # Create Solver object
    solver = Solver(prolog_file=prolog_file, level_w=level_w, level_h=level_h,
                    min_perc_blocks=min_perc_blocks, level_sections=level_sections,
                    print_level_stats=print_level_stats, save=save, validate=validate,
                    start_tile_id=prolog_file_info.get('start_tile_id'),
                    block_tile_id=prolog_file_info.get('block_tile_id'),
                    goal_tile_id=prolog_file_info.get('goal_tile_id'))

    # Set up keyboard interrupt handlers
    signal.signal(signal.SIGINT, handler=lambda s, f: keyboard_interrupt_handler(signal=s, frame=f, solver=solver))
    signal.signal(signal.SIGTSTP, handler=lambda s, f: keyboard_interrupt_handler(signal=s, frame=f, solver=solver))

    # Run clingo solver
    solver.solve(max_sol=max_sol)

    # Validate generated levels
    solver.end_and_validate()


if __name__ == "__main__":

    # main('level_saved_files_block/prolog_files/sample_mini.pl', level_w=9, level_h=6, min_perc_blocks=65,
    #      level_sections=2, max_sol=0, print_level_stats=False, save=True, validate=True)
    #
    # main('level_saved_files_block/prolog_files/mario-icarus-1.pl', level_w=30, level_h=16, min_perc_blocks=None,
    #      level_sections=4, max_sol=10, print_level_stats=False, save=True, validate=True)
    #
    # main('level_saved_files_block/prolog_files/mario-icarus-1.pl', level_w=18, level_h=100, min_perc_blocks=None,
    #      level_sections=4, max_sol=10, print_level_stats=False, save=True, validate=True)
    #
    # exit(0)

    parser = argparse.ArgumentParser(description='Run solver and create new levels from valid answer sets')
    parser.add_argument('prolog_file', type=str, help="File path of the prolog file to use")
    parser.add_argument('level_w', type=int, help="Number of tiles in a row")
    parser.add_argument('level_h', type=int, help="Number of tiles in a column")
    parser.add_argument('--min_perc_blocks', type=int, default=None, help='Minimum percentage of block tiles in a level')
    parser.add_argument('--level_sections', type=int, default=2, help="Number of sections to split the gen level into. Start tile will be in first section, goal tile in last section.")
    parser.add_argument('--max_sol', type=int, default=0, help="Max number of answer sets to return. 0 = all solutions")
    parser.add_argument('--print_level_stats', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--save', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--validate', const=True, nargs='?', type=bool, default=False, help="Validate generated levels")
    args = parser.parse_args()

    main(args.prolog_file, args.level_w, args.level_h, args.min_perc_blocks, args.level_sections,
         args.max_sol, args.print_level_stats, args.save, args.validate)
