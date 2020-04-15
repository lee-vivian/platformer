from math import inf
import argparse

from solver import Solver
from utils import get_filepath, read_pickle

"""
Run clingo solver on the given prolog file with the specified params
"""

# TODO UPDATE END AND VALIDATE
# def end_and_validate(answer_set_count, gen_level_dict, id_metatile_map, player_img, start_time):
#     print("Num Levels Generated: %d" % answer_set_count)
#     if gen_level_dict is not None:
#         solver_validate.main(gen_level_dict, id_metatile_map, player_img)
#     end_time = datetime.now()
#     print("Total Runtime: %s" % str(end_time-start_time))


def main(prolog_file, level_w, level_h, min_perc_blocks, start_bottom_left, max_sol, print_level_stats, save, validate):

    player_img, prolog_filename = Solver.parse_prolog_filepath(prolog_file)
    level_saved_files_dir = "level_saved_files_%s/" % player_img
    all_prolog_info_file = get_filepath(level_saved_files_dir + "prolog_files", "all_prolog_info.pickle")
    all_prolog_info_map = read_pickle(all_prolog_info_file)
    prolog_file_info = all_prolog_info_map.get(prolog_filename)

    # Create Solver object
    solver = Solver(prolog_file=prolog_file, level_w=level_w, level_h=level_h, min_perc_blocks=min_perc_blocks,
                    start_bottom_left=start_bottom_left, print_level_stats=print_level_stats, save=save,
                    start_tile_id=prolog_file_info.get('start_tile_id'), block_tile_id=prolog_file_info.get('block_tile_id'),
                    goal_tile_id=prolog_file_info.get('goal_tile_id'))

    # Run clingo solver
    solver.solve(max_sol)


if __name__ == "__main__":

    # prolog_files = ['level_saved_files_block/prolog_files/sample_mini.pl',
    #                 'level_saved_files_block/prolog_files/mario-icarus-1.pl',
    #                 'level_saved_files_block/prolog_files/mario-all.pl']
    #
    # main('level_saved_files_block/prolog_files/mario-all.pl', level_w=50, level_h=6, min_perc_blocks=None,
    #      start_bottom_left=True, max_sol=2, skip_print_answers=False, print_tiles_per_level=True, save=True,
    #      validate=True)
    #
    # main('level_saved_files_block/prolog_files/mario-all.pl', level_w=50, level_h=6, min_perc_blocks=65,
    #      start_bottom_left=True, max_sol=2, skip_print_answers=False, print_tiles_per_level=True, save=True,
    #      validate=True)
    #
    # main('level_saved_files_block/prolog_files/mario-icarus-1.pl', level_w=30, level_h=6, min_perc_blocks=None,
    #      start_bottom_left=True, max_sol=2, skip_print_answers=False, print_tiles_per_level=True, save=True,
    #      validate=True)
    #
    # main('level_saved_files_block/prolog_files/mario-icarus-1.pl', level_w=18, level_h=100, min_perc_blocks=None,
    #      start_bottom_left=True, max_sol=2, skip_print_answers=False, print_tiles_per_level=True, save=True,
    #      validate=True)
    #
    # exit(0)

    parser = argparse.ArgumentParser(description='Run solver and create new levels from valid answer sets')
    parser.add_argument('prolog_file', type=str, help="File path of the prolog file to use")
    parser.add_argument('level_w', type=int, help="Number of tiles in a row")
    parser.add_argument('level_h', type=int, help="Number of tiles in a column")
    parser.add_argument('--min_perc_blocks', type=int, default=None, help='Minimum percentage of block tiles in a level')
    parser.add_argument('--start_bottom_left', const=True, nargs='?', type=bool, default=False, help='Fix start position to the bottom left of the level')
    parser.add_argument('--max_sol', type=int, default=inf, help="Max number of answer sets to return. Default = inf")
    parser.add_argument('--print_level_stats', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--save', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--validate', const=True, nargs='?', type=bool, default=False, help="Validate generated levels")
    args = parser.parse_args()

    main(args.prolog_file, args.level_w, args.level_h, args.min_perc_blocks, args.start_bottom_left,
         args.max_sol, args.print_level_stats, args.save, args.validate)
