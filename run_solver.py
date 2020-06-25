import signal
import argparse
import os

from model.metatile import METATILE_TYPES
from solver import Solver
from utils import get_filepath, read_pickle, read_json, error_exit, get_basepath_filename

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


def get_tile_ids_dictionary(prolog_file_info):
    tile_types = METATILE_TYPES.copy()
    tile_types.remove("empty")
    tile_ids = {}
    for tile_type in tile_types:
        tile_ids[tile_type] = prolog_file_info.get('%s_tile_ids' % tile_type)
    return tile_ids


def check_tile_type_exists_in_prolog(tile_type, prolog_file_info, error_msg):
    if len(prolog_file_info.get('%s_tile_ids' % tile_type)) < 1:
        error_exit("tile type (%s) not found in prolog file; %s" % (tile_type, error_msg))


def setup_tile_freq_range(tile_type, min_tiles, max_tiles, lowest, highest):
    if min_tiles is not None and not (lowest <= min_tiles <= highest):
        error_exit("Specified min freq (%d) for '%s' tiles must be in range [%d,%d]" % (min_tiles, tile_type, lowest, highest))
    if max_tiles is not None and not (lowest <= max_tiles <= highest):
        error_exit("Specified max freq (%d) for '%s' tiles be in range [%d,%d]" % (max_tiles, tile_type, lowest, highest))
    if min_tiles is not None and max_tiles is not None and min_tiles > max_tiles:
        error_exit("Specified min freq (%d) for '%s' tiles must be <= max freq (%d)" % (min_tiles, tile_type, max_tiles))

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

    # ----- SOFT CONSTRAINTS -----
    soft_constraints = {}
    if config.get('soft_constraints') is not None:
        soft_constraints = config.get('soft_constraints')

    # ----- SPECIFY NUM TILE RANGES (for a certain type) -----
    num_tile_ranges = {}
    lo, hi = 0, level_w * level_h
    for tile_type in METATILE_TYPES:
        num_tile_ranges[tile_type] = (lo, hi)

    if config.get('num_tile_ranges') is not None:
        for tile_type, range_str in config['num_tile_ranges'].items():
            check_tile_type_exists_in_prolog(tile_type, prolog_file_info, 'cannot force num tile range %s' % range_str)
            min_tiles, max_tiles = eval(range_str)
            num_tile_ranges[tile_type] = setup_tile_freq_range(tile_type, min_tiles, max_tiles, lo, hi)

        # Check if total min tiles > total tiles
        min_total = 0
        for tile_type, tile_range in num_tile_ranges.items():
            min_total += tile_range[0]
        if min_total > level_w * level_h:
            error_exit("Sum of min tiles (%d) in specified num_tile_ranges cannot exceed the total number of tiles "
                       "available in the generated level (%d)" % (min_total, level_w*level_h))

    # ----- SPECIFY PERCENT TILE RANGES (for a certain type) -----
    perc_tile_ranges = {}
    lo, hi = 0, 100
    for tile_type in METATILE_TYPES:
        perc_tile_ranges[tile_type] = (lo, hi)

    if config.get('perc_tile_ranges') is not None:
        for tile_type, range_str in config['perc_tile_ranges'].items():
            check_tile_type_exists_in_prolog(tile_type, prolog_file_info, 'cannot force perc tile range %s' % range_str)
            min_perc_tiles, max_perc_tiles = eval(range_str)
            perc_tile_ranges[tile_type] = setup_tile_freq_range(tile_type, min_perc_tiles, max_perc_tiles, lo, hi)

        # Check if total min perc tiles > 100%
        min_perc_total = 0
        for tile_type, tile_range in perc_tile_ranges.items():
            min_perc_total += tile_range[0]
        if min_perc_total > 100:
            error_exit("Sum of min perc tiles (%d) in specified perc_tile_ranges cannot exceed 100%%" % min_perc_total)

    # ----- SPECIFY PERCENT TILE RANGES (from a certain level) -----
    level_ids_map = prolog_file_info.get('level_ids_map')
    perc_level_ranges = {}
    lo, hi = 0, 100
    for level, ids in level_ids_map.items():
        perc_level_ranges[level] = (lo, hi)

    if config.get('perc_level_ranges') is not None:
        for level, range_str in config['perc_level_ranges'].items():
            if level_ids_map.get(level) is None:
                error_exit("The tileset does not contain tiles from level (%s) (specified in perc_level_"
                           "ranges). Valid levels are: %s" % (level, str(list(level_ids_map.keys()))))
            min_perc_level, max_perc_level = eval(range_str)
            perc_level_ranges[level] = setup_tile_freq_range(level, min_perc_level, max_perc_level, lo, hi)

        # Check if total min perc levels > 100%
        min_perc_level_total = 0
        for level, tile_range in perc_level_ranges.items():
            min_perc_level_total += tile_range[0]
        if min_perc_level_total > 100:
            error_exit("Sum of min perc tiles (%d) from each level specified in perc_level_ranges cannot exceed 100%%" % min_perc_level_total)

    # ----- SPECIFY START/GOAL POSITION RANGES -----
    tile_position_ranges = {
        'start_column': (0, level_w-1),
        'start_row': (0, level_h-1),
        'goal_column': (0, level_w-1),
        'goal_row': (0, level_h-1)
    }

    if config.get('tile_position_ranges') is not None:
        for position, range_str in config['tile_position_ranges'].items():
            if tile_position_ranges.get(position) is None:
                error_exit("%s tile position does not exist. Position must be one of %s" % (position, str(list(tile_position_ranges.keys()))))
            level_max = level_w if 'column' in position else level_h
            min_index, max_index = eval(range_str)
            min_index, max_index = setup_tile_position_range(min_index, max_index, level_max)
            tile_position_ranges[position] = (min_index, max_index)

    # ----- SPECIFY IF START AND/OR GOAL TILE MUST BE ON GROUND -----
    require_start_on_ground = False
    require_goal_on_ground = False

    if config.get('require_start_on_ground') is not None:
        require_start_on_ground = eval(config['require_start_on_ground'])

    if config.get('require_goal_on_ground') is not None:
        require_goal_on_ground = eval(config['require_goal_on_ground'])

    # ----- SPECIFY RANGE NUMBER OF GAPS (PITS) ALLOWED -----
    lo, hi = 0, level_w
    num_gaps_range = (lo, hi)

    if config.get('num_gaps_range') is not None:
        min_gaps, max_gaps = eval(config['num_gaps_range'])
        min_gaps, max_gaps = setup_tile_freq_range('gap', min_gaps, max_gaps, lo, hi)
        num_gaps_range = (min_gaps, max_gaps)

    # ----- SPECIFY IF ALL PLATFORM OR BONUS TILES MUST BE REACHABLE -----
    require_all_platforms_reachable = False
    require_all_bonus_tiles_reachable = False
    if config.get('require_all_platforms_reachable') is not None:
        require_all_platforms_reachable = eval(config['require_all_platforms_reachable'])
    if config.get('require_all_bonus_tiles_reachable') is not None:
        require_all_bonus_tiles_reachable = eval(config['require_all_bonus_tiles_reachable'])

    return {
        'level_w': level_w,                                     # int
        'level_h': level_h,                                     # int
        'forced_tiles': forced_tiles,                           # {type: list-of-tile-coords}\
        'soft_constraints': soft_constraints,                   # {constraint_type: constraint_value}
        'num_tile_ranges': num_tile_ranges,                     # { type: (min, max) }
        'perc_tile_ranges': perc_tile_ranges,                   # { type: (min, max) }
        'perc_level_ranges': perc_level_ranges,                 # { level: (min, max) }
        'tile_position_ranges': tile_position_ranges,           # { position: (min, max) }
        'require_start_on_ground': require_start_on_ground,     # bool
        'require_goal_on_ground': require_goal_on_ground,       # bool
        'num_gaps_range': num_gaps_range,                        # (min, max)
        'require_all_platforms_reachable': require_all_platforms_reachable,  # bool
        'require_all_bonus_tiles_reachable': require_all_bonus_tiles_reachable  # bool
    }


def main(prolog_file, config_file, max_sol, threads, print_level, save, validate):

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
    config_filename = get_basepath_filename(config_file, 'json')
    config_file_contents = read_json(config_file)
    config = config_file_contents['config']
    config = get_solver_config(config, prolog_file_info)

    # Create tile ids dictionary
    tile_ids = get_tile_ids_dictionary(prolog_file_info)

    # Create Solver object
    solver = Solver(prolog_file=prolog_file,
                    config=config,
                    config_filename=config_filename,
                    tile_ids=tile_ids,
                    level_ids_map=prolog_file_info.get('level_ids_map'),
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
    parser.add_argument('--print_level', const=True, nargs='?', type=bool, default=False, help="Print structural txt layer of generated levels")
    parser.add_argument('--save', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--validate', const=True, nargs='?', type=bool, default=False, help="Validate generated levels")
    args = parser.parse_args()

    main(prolog_file=args.prolog_file, config_file=args.config_file, max_sol=args.max_sol, threads=args.threads,
         print_level=args.print_level, save=args.save, validate=args.validate)
