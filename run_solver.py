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

def setup_min_max_num_tiles(prolog_tile_key, prolog_file_info, min_tiles, max_tiles, num_tiles):
    min_specified = min_tiles is not None and min_tiles > 0
    max_specified = max_tiles is not None and max_tiles < num_tiles

    if min_specified or max_specified and prolog_file_info.get(prolog_tile_key) is None:
        error_exit("specified prolog file does not contain %s" % prolog_tile_key)

    if min_specified and max_specified and min_tiles > max_tiles:
        error_exit("min tiles must be < max tiles for %s type tiles" % prolog_tile_key)

    min_num_tiles = 0 if min_tiles is None else min_tiles
    max_num_tiles = num_tiles if max_tiles is None else max_tiles

    return min_num_tiles, max_num_tiles


def main(prolog_file, level_w, level_h, min_perc_blocks, max_perc_blocks, min_bonus, max_bonus, min_one_way, max_one_way,
         no_pit, start_min, start_max, goal_min, goal_max, max_sol, threads, print_level_stats, print, save, validate):

    player_img, prolog_filename = Solver.parse_prolog_filepath(prolog_file)
    level_saved_files_dir = "level_saved_files_%s/" % player_img
    all_prolog_info_file = get_filepath(level_saved_files_dir + "prolog_files", "all_prolog_info.pickle")
    all_prolog_info_map = read_pickle(all_prolog_info_file)
    prolog_file_info = all_prolog_info_map[prolog_filename]

    if threads < 1:
        error_exit("--threads must be an integer >= 1")

    # Set up min and max num tiles (bonus, one-way platform)
    min_bonus, max_bonus = setup_min_max_num_tiles('bonus_tile_id', prolog_file_info, min_bonus, max_bonus, num_tiles=level_w * level_h)
    min_one_way, max_one_way = setup_min_max_num_tiles('one_way_tile_ids', prolog_file_info, min_one_way, max_one_way, num_tiles=level_w * level_h)

    # Set up start and goal tile column ranges
    start_min, start_max = setup_tile_col_range(start_min, start_max, level_w)
    goal_min, goal_max = setup_tile_col_range(goal_min, goal_max, level_w)
            
    # Create Solver object
    solver = Solver(prolog_file=prolog_file, level_w=level_w, level_h=level_h,
                    min_perc_blocks=min_perc_blocks, max_perc_blocks=max_perc_blocks,
                    min_bonus=min_bonus, max_bonus=max_bonus, min_one_way=min_one_way, max_one_way=max_one_way,
                    no_pit=no_pit, start_min=start_min, start_max=start_max, goal_min=goal_min, goal_max=goal_max,
                    print_level_stats=print_level_stats, print=print, save=save, validate=validate,
                    start_tile_id=prolog_file_info.get('start_tile_id'),
                    block_tile_id=prolog_file_info.get('block_tile_id'),
                    goal_tile_id=prolog_file_info.get('goal_tile_id'),
                    bonus_tile_id=prolog_file_info.get('bonus_tile_id'),
                    one_way_tile_ids=prolog_file_info.get('one_way_tile_ids'))

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
    parser.add_argument('--min_one_way', type=int, default=None, help='Minimum number of one-way platform tiles in a level')
    parser.add_argument('--max_one_way', type=int, default=None, help='Maximum number of one-way platform tiles in a level')
    parser.add_argument('--no_pit', const=True, nargs='?', type=bool, default=False, help='Force all floor tiles to be blocks')
    parser.add_argument('--start_min', type=int, default=None, help="Min column index for the start tile")
    parser.add_argument('--start_max', type=int, default=None, help="Max column index for the start tile")
    parser.add_argument('--goal_min', type=int, default=None, help="Min column index for the goal tile")
    parser.add_argument('--goal_max', type=int, default=None, help="Max column index for the goal tile")
    parser.add_argument('--max_sol', type=int, default=1, help="Max number of answer sets to return")
    parser.add_argument('--threads', type=int, default=1, help="Number of threads to run the solver on")
    parser.add_argument('--print_level_stats', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--print', const=True, nargs='?', type=bool, default=False, help="Print structural txt layer of generated levels")
    parser.add_argument('--save', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--validate', const=True, nargs='?', type=bool, default=False, help="Validate generated levels")
    args = parser.parse_args()

    main(prolog_file=args.prolog_file, level_w=args.level_w, level_h=args.level_h,
         min_perc_blocks=args.min_perc_blocks, max_perc_blocks=args.max_perc_blocks,
         min_bonus=args.min_bonus, max_bonus=args.max_bonus, min_one_way=args.min_one_way, max_one_way=args.max_one_way,
         no_pit=args.no_pit, start_min=args.start_min, start_max=args.start_max, goal_min=args.goal_min, goal_max=args.goal_max,
         max_sol=args.max_sol, threads=args.threads,
         print_level_stats=args.print_level_stats, print=args.print, save=args.save, validate=args.validate)
