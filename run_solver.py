import signal
import argparse
import os

from model.metatile import METATILE_TYPES
from solver import Solver
from utils import get_filepath, read_pickle, read_json, error_exit

"""
Run clingo solver on the given prolog file with the specified params
"""


def keyboard_interrupt_handler(signal, frame, solver):
    print("----- KEYBOARD INTERRUPT -----")
    solver.end_and_validate()
    exit(0)


def get_prolog_file_info(prolog_file):
    player_img, prolog_filename = Solver.parse_prolog_filepath(prolog_file)
    all_prolog_info_file = get_filepath("level_saved_files_%s/prolog_files" % player_img, "all_prolog_info.pickle")
    all_prolog_info_map = read_pickle(all_prolog_info_file)
    prolog_file_info = all_prolog_info_map[prolog_filename]
    return prolog_file_info


def check_tile_type_exists_in_prolog(tile_type, prolog_file_info, error_msg):
    if len(prolog_file_info.get('%s_tile_ids' % tile_type)) < 1:
        error_exit("tile type (%s) not found in prolog file; %s" % (tile_type, error_msg))


def setup_tile_freq_range(tile_type, min_tiles, max_tiles, lowest, highest):
    if min_tiles is not None and not (lowest <= min_tiles <= highest):
        error_exit("Specified min (%d) for type '%s' must be in range [%d,%d]" % (min_tiles, tile_type, lowest, highest))
    if max_tiles is not None and not (lowest <= max_tiles <= highest):
        error_exit("Specified max (%d) for type '%s' must be in range [%d,%d]" % (max_tiles, tile_type, lowest, highest))
    if min_tiles is not None and max_tiles is not None and min_tiles > max_tiles:
        error_exit("Specified min (%d) for type '%s' must be <= max (%d)" % (min_tiles, tile_type, max_tiles))

    min_tiles = lowest if min_tiles is None else min_tiles
    max_tiles = highest if max_tiles is None else max_tiles
    return min_tiles, max_tiles


def setup_tile_position_range(min_index, max_index, level_max):
    if min_index is not None and not (0 <= min_index <= level_max):
        error_exit("invalid min index (%d) given, min index must be in range [0,%d)" % (min_index, level_max))
    if max_index is not None and not (0 <= max_index <= level_max):
        error_exit("invalid max index (%d) given, max index must be in range [0,%d)" % (max_index, level_max))
    if min_index is not None and max_index is not None and min_index > max_index:
        error_exit("min index (%d) cannot exceed max index (%d)" % (min_index, max_index))

    min_index = 0 if min_index is None else min_index
    max_index = level_max - 1 if max_index is None else max_index
    return min_index, max_index


def get_solver_config(config, prolog_file_info):

    # ----- LEVEL DIMENSIONS -----
    level_w = config['level_dimensions']['width']
    level_h = config['level_dimensions']['height']

    # ----- FORCE TILE TYPE (tiles at specified coords must be a certain type) -----
    forced_tiles = {}
    if config.get('force_tile_type') is not None:
        for tile_type, coord_strs in config['force_tile_type'].items():
            check_tile_type_exists_in_prolog(tile_type, prolog_file_info, 'cannot force tile type (%s: %s)' % (tile_type, coord_strs))
            forced_tiles[tile_type] = eval(coord_strs)

    # ----- FORCE TILE REACHABILITY (tiles at specified coords must be reachable)
    reachable_tiles = []
    if config.get('reachable_tiles') is not None:
        reachable_tiles += eval(config['reachable_tiles'])

    # ----- SPECIFY NUM TILE RANGES (for a certain type) -----
    num_tile_ranges = {}
    num_tile_lowest = 0,
    num_tile_highest = level_w * level_h
    for tile_type in METATILE_TYPES:
        num_tile_ranges[tile_type] = {'min': num_tile_lowest, 'max': num_tile_highest}

    if config.get('num_tile_ranges') is not None:
        for tile_type, range_str in config['num_tile_ranges'].items():
            check_tile_type_exists_in_prolog(tile_type, prolog_file_info, 'cannot force num tile range %s' % range_str)
            min_tiles, max_tiles = eval(range_str)
            min_tiles, max_tiles = setup_tile_freq_range(tile_type, min_tiles, max_tiles, num_tile_lowest, num_tile_highest)
            num_tile_ranges[tile_type] = {'min': min_tiles, 'max': max_tiles}

        # Check if total min tiles > total tiles
        min_total = 0
        for tile_type, tile_range_dict in num_tile_ranges.items():
            min_total += tile_range_dict['min']
        if min_total > level_w * level_h:
            error_exit("Sum of min tiles (%d) in specified num_tile_ranges cannot exceed the total number of tiles "
                       "available in the generated level (%d)" % (min_total, level_w*level_h))

    # ----- SPECIFY PERCENT TILE RANGES (for a certain type) -----
    perc_tile_ranges = {}
    perc_tile_lowest = 0
    perc_tile_highest = 100
    for tile_type in METATILE_TYPES:
        perc_tile_ranges[tile_type] = {'min': 0, 'max': 100}

    if config.get('perc_tile_ranges') is not None:
        for tile_type, range_str in config['perc_tile_ranges'].items():
            check_tile_type_exists_in_prolog(tile_type, prolog_file_info, 'cannot force perc tile range %s' % range_str)
            min_perc_tiles, max_perc_tiles = eval(range_str)
            min_perc_tiles, max_perc_tiles = setup_tile_freq_range(tile_type, min_perc_tiles, max_perc_tiles, perc_tile_lowest, perc_tile_highest)
            perc_tile_ranges[tile_type] = {'min': min_perc_tiles, 'max': max_perc_tiles}

        # Check if total min perc tiles > 100%
        min_perc_total = 0
        for tile_type, tile_range_dict in perc_tile_ranges.items():
            min_perc_total += tile_range_dict['min']
        if min_perc_total > 100:
            error_exit("Sum of min perc tiles (%d) in specified perc_tile_ranges cannot exceed 100%%" % min_perc_total)

    # TODO add range % of tiles from specified levels

    # ----- SPECIFY START/GOAL POSITION RANGES -----
    tile_position_ranges = {
        'start_column': {'min': 0, 'max': level_w-1},
        'start_row': {'min': 0, 'max': level_h-1},
        'goal_column': {'min': 0, 'max': level_w-1},
        'goal_row': {'min': 0, 'max': level_h-1}
    }

    if config.get('tile_position_ranges') is not None:
        for position, range_str in config['tile_position_ranges'].items():
            if tile_position_ranges.get(position) is None:
                error_exit("%s tile position does not exist. Position must be one of %s" % (position, str(list(tile_position_ranges.keys()))))
            level_max = level_w if 'column' in position else level_h
            min_index, max_index = eval(range_str)
            min_index, max_index = setup_tile_position_range(min_index, max_index, level_max)
            tile_position_ranges[position] = {'min': min_index, 'max': max_index}

    # ----- SPECIFY IF PITS ARE ALLOWED -----
    allow_pits = True
    if config.get('allow_pits') is not None:
        allow_pits = eval(config['allow_pits'])

    return {
        'level_w': level_w,                             # int
        'level_h': level_h,                             # int
        'forced_tiles': forced_tiles,                   # {type: list-of-tile-coords}
        'reachable_tiles': reachable_tiles,             # list-of-tile-coords
        'num_tile_ranges': num_tile_ranges,             # { type: {'min': min, 'max': max} }
        'perc_tile_ranges': perc_tile_ranges,           # { type: {'min': min, 'max': max} }
        'tile_position_ranges': tile_position_ranges,   # { position: {'min': min, 'max': max} }
        'allow_pits': allow_pits                        # bool
    }


def main(prolog_file, config_file, max_sol, threads, print_level_stats, print_level, save, validate):

    if not os.path.exists(prolog_file):
        error_exit("prolog_file does not exist: %s" % prolog_file)

    if not os.path.exists(config_file):
        error_exit("config_file does not exist: %s" % config_file)

    if max_sol < 1:
        error_exit("--max_sol must be an integer >= 1")

    if threads < 1:
        error_exit("--threads must be an integer >= 1")

    # Parse the prolog file
    prolog_file_info = get_prolog_file_info(prolog_file)

    # Parse the config file
    config_file_contents = read_json(config_file)
    config = config_file_contents['config']
    config = get_solver_config(config, prolog_file_info)

    # Create tile ids dictionary
    tile_types = ['block', 'bonus', 'one_way_platform', 'start', 'goal']
    tile_ids = {}
    for tile_type in tile_types:
        tile_ids[tile_type] = prolog_file_info.get('%s_tile_ids' % tile_type)

    # Create Solver object
    solver = Solver(prolog_file=prolog_file,
                    config=config,
                    config_filename=os.path.basename(config_file),
                    tile_ids=tile_ids,
                    print_level_stats=print_level_stats,
                    print_level=print_level,
                    save=save,
                    validate=validate)

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
    parser.add_argument('config_file', type=str, help="File path of the json file to use to specify design decisions")
    parser.add_argument('--max_sol', type=int, default=1, help="Max number of answer sets to return")
    parser.add_argument('--threads', type=int, default=1, help="Number of threads to run the solver on")
    parser.add_argument('--print_level_stats', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--print_level', const=True, nargs='?', type=bool, default=False, help="Print structural txt layer of generated levels")
    parser.add_argument('--save', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--validate', const=True, nargs='?', type=bool, default=False, help="Validate generated levels")
    args = parser.parse_args()

    main(prolog_file=args.prolog_file, config_file=args.config_file, max_sol=args.max_sol, threads=args.threads,
         print_level_stats=args.print_level_stats, print_level=args.print_level, save=args.save, validate=args.validate)
