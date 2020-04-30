import signal
import argparse

from solver import Solver
from utils import get_filepath, read_pickle, error_exit

"""
Run clingo solver on the given prolog file with the specified params
"""


def keyboard_interrupt_handler(signal, frame, solver):
    print("----- KEYBOARD INTERRUPT -----")
    solver.end_and_validate()
    exit(0)


def main(prolog_file, level_w, level_h, min_perc_blocks, max_perc_blocks, min_bonus, max_bonus, no_pits, level_sections,
         max_sol, print_level_stats, save, validate):

    player_img, prolog_filename = Solver.parse_prolog_filepath(prolog_file)
    level_saved_files_dir = "level_saved_files_%s/" % player_img
    all_prolog_info_file = get_filepath(level_saved_files_dir + "prolog_files", "all_prolog_info.pickle")
    all_prolog_info_map = read_pickle(all_prolog_info_file)
    prolog_file_info = all_prolog_info_map[prolog_filename]

    # Set up min and max num bonus tiles
    if min_bonus is not None and min_bonus > 0 and prolog_file_info.get('bonus_tile_id') is None:
        error_exit("specified prolog file does not contain bonus tile ids")

    if min_bonus is not None and max_bonus is not None and min_bonus > max_bonus:
        error_exit("min bonus tiles must be < max bonus tiles")

    if min_bonus is None:
        min_bonus = 0

    if max_bonus is None:
        max_bonus = level_w * level_h
        if max_perc_blocks is not None:
            max_bonus = int(max_bonus * (max_perc_blocks / 100))

    # Create Solver object
    solver = Solver(prolog_file=prolog_file, level_w=level_w, level_h=level_h,
                    min_perc_blocks=min_perc_blocks, max_perc_blocks=max_perc_blocks,
                    min_bonus=min_bonus, max_bonus=max_bonus, no_pits=no_pits,
                    level_sections=level_sections, print_level_stats=print_level_stats, save=save, validate=validate,
                    start_tile_id=prolog_file_info.get('start_tile_id'),
                    block_tile_id=prolog_file_info.get('block_tile_id'),
                    goal_tile_id=prolog_file_info.get('goal_tile_id'),
                    bonus_tile_id=prolog_file_info.get('bonus_tile_id'))

    # Set up keyboard interrupt handlers
    signal.signal(signal.SIGINT, handler=lambda s, f: keyboard_interrupt_handler(signal=s, frame=f, solver=solver))
    signal.signal(signal.SIGTSTP, handler=lambda s, f: keyboard_interrupt_handler(signal=s, frame=f, solver=solver))

    # Run clingo solver
    solver.solve(max_sol=max_sol)

    # Validate generated levels
    solver.end_and_validate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run solver and create new levels from valid answer sets')
    parser.add_argument('prolog_file', type=str, help="File path of the prolog file to use")
    parser.add_argument('level_w', type=int, help="Number of tiles in a row")
    parser.add_argument('level_h', type=int, help="Number of tiles in a column")
    parser.add_argument('--min_perc_blocks', type=int, default=None, help='Minimum percentage of block tiles in a level')
    parser.add_argument('--max_perc_blocks', type=int, default=None, help='Maximum percentage of block tiles in a level')
    parser.add_argument('--min_bonus', type=int, default=None, help='Minimum number of bonus tiles in a level')
    parser.add_argument('--max_bonus', type=int, default=None, help='Maximum number of bonus tiles in a level')
    parser.add_argument('--no_pits', const=True, nargs='?', type=bool, default=False, help='Force all floor tiles to be blocks')
    parser.add_argument('--level_sections', type=int, default=1, help="Number of sections to split the gen level into. Start tile will be in first section, goal tile in last section.")
    parser.add_argument('--max_sol', type=int, default=0, help="Max number of answer sets to return. 0 = all solutions")
    parser.add_argument('--print_level_stats', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--save', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--validate', const=True, nargs='?', type=bool, default=False, help="Validate generated levels")
    args = parser.parse_args()

    main(args.prolog_file, args.level_w, args.level_h, args.min_perc_blocks, args.max_perc_blocks,
         args.min_bonus, args.max_bonus, args.no_pits, args.level_sections, args.max_sol, args.print_level_stats,
         args.save, args.validate)
