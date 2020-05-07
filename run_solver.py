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
    
    
def setup_tile_col_range(min_col, max_col, level_w):
    if min_col is not None and (min_col < 0 or min_col >= level_w):
        error_exit("invalid min_col column index given, min_col must be in range [0,%d)" % level_w)
    
    if max_col is not None and (max_col < 0 or max_col >= level_w):
        error_exit("invalid max_col column index given, max_col must be in range [0,%d)" % level_w)
        
    if min_col is not None and max_col is not None and min_col > max_col:
        error_exit("min_col column index (%d) cannot exceed max_col column index (%d)" % (min_col, max_col))
        
    min_col = 0 if min_col is None else min_col
    max_col = level_w - 1 if max_col is None else max_col
    
    return min_col, max_col


def main(prolog_file, level_w, level_h, min_perc_blocks, max_perc_blocks, min_bonus, max_bonus, no_pit,
         start_min, start_max, goal_min, goal_max, max_sol, threads, print_level_stats, print, save, validate, n):

    player_img, prolog_filename = Solver.parse_prolog_filepath(prolog_file)
    level_saved_files_dir = "level_saved_files_%s/" % player_img
    all_prolog_info_file = get_filepath(level_saved_files_dir + "prolog_files", "all_prolog_info.pickle")
    all_prolog_info_map = read_pickle(all_prolog_info_file)
    prolog_file_info = all_prolog_info_map[prolog_filename]

    if threads < 1:
        error_exit("--threads must be an integer >= 1")

    if n <= 0:
        error_exit("--n must be an integer greater than 0")

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
            
    # Set up start and goal tile column ranges
    start_min, start_max = setup_tile_col_range(start_min, start_max, level_w)
    goal_min, goal_max = setup_tile_col_range(goal_min, goal_max, level_w)
            
    # Create Solver object
    solver = Solver(prolog_file=prolog_file, level_w=level_w, level_h=level_h,
                    min_perc_blocks=min_perc_blocks, max_perc_blocks=max_perc_blocks,
                    min_bonus=min_bonus, max_bonus=max_bonus, no_pit=no_pit,
                    start_min=start_min, start_max=start_max, goal_min=goal_min, goal_max=goal_max,
                    print_level_stats=print_level_stats, print=print, save=save, validate=validate, n=n,
                    start_tile_id=prolog_file_info.get('start_tile_id'),
                    block_tile_id=prolog_file_info.get('block_tile_id'),
                    goal_tile_id=prolog_file_info.get('goal_tile_id'),
                    bonus_tile_id=prolog_file_info.get('bonus_tile_id'))

    # Set up keyboard interrupt handlers
    signal.signal(signal.SIGINT, handler=lambda s, f: keyboard_interrupt_handler(signal=s, frame=f, solver=solver))
    signal.signal(signal.SIGTSTP, handler=lambda s, f: keyboard_interrupt_handler(signal=s, frame=f, solver=solver))

    # Run clingo solver
    solver.solve(max_sol=max_sol, threads=threads)

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
    parser.add_argument('--no_pit', const=True, nargs='?', type=bool, default=False, help='Force all floor tiles to be blocks')
    parser.add_argument('--start_min', type=int, default=None, help="Min column index for the start tile")
    parser.add_argument('--start_max', type=int, default=None, help="Max column index for the start tile")
    parser.add_argument('--goal_min', type=int, default=None, help="Min column index for the goal tile")
    parser.add_argument('--goal_max', type=int, default=None, help="Max column index for the goal tile")
    parser.add_argument('--max_sol', type=int, default=1000000, help="Max number of answer sets to return. 0 = all solutions")
    parser.add_argument('--threads', type=int, default=1, help="Number of threads to run the solver on")
    parser.add_argument('--print_level_stats', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--print', const=True, nargs='?', type=bool, default=False, help="Print structural txt layer of generated levels")
    parser.add_argument('--save', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--validate', const=True, nargs='?', type=bool, default=False, help="Validate generated levels")
    parser.add_argument('--n', type=int, help="Save and/or validate every nth answer set", default=1000)
    args = parser.parse_args()

    main(prolog_file=args.prolog_file, level_w=args.level_w, level_h=args.level_h,
         min_perc_blocks=args.min_perc_blocks, max_perc_blocks=args.max_perc_blocks,
         min_bonus=args.min_bonus, max_bonus=args.max_bonus, no_pit=args.no_pit,
         start_min=args.start_min, start_max=args.start_max, goal_min=args.goal_min, goal_max=args.goal_max,
         max_sol=args.max_sol, threads=args.threads, print_level_stats=args.print_level_stats,
         print=args.print, save=args.save, validate=args.validate, n=args.n)
