import clingo
import argparse
from datetime import datetime
from math import inf

import solver_validate
from model.solver import Solver
from utils import get_filepath, read_pickle, write_pickle, write_file


# TODO UPDATE END AND VALIDATE
# def end_and_validate(answer_set_count, gen_level_dict, id_metatile_map, player_img, start_time):
#     print("Num Levels Generated: %d" % answer_set_count)
#     if gen_level_dict is not None:
#         solver_validate.main(gen_level_dict, id_metatile_map, player_img)
#     end_time = datetime.now()
#     print("Total Runtime: %s" % str(end_time-start_time))


def print_num_tiles(tile_id_extra_info_coords_map, start_tile_id, block_tile_id, goal_tile_id):
    num_tiles, num_start_tiles, num_block_tiles, num_goal_tiles = 0, 0, 0, 0

    for (tile_id, extra_info), coords in tile_id_extra_info_coords_map.items():
        len_coords = len(coords)
        num_tiles += len_coords
        if tile_id == block_tile_id:
            num_block_tiles += len_coords
        elif tile_id == start_tile_id:
            num_start_tiles += len_coords
        elif tile_id == goal_tile_id:
            num_goal_tiles += len_coords

    print("Total tiles: %d (%d/100)" % (num_tiles, num_tiles/num_tiles * 100))
    print("Block tiles:  %d (%d/100)" % (num_block_tiles, num_block_tiles/num_tiles * 100))
    print("Start tiles:  %d (%d/100)" % (num_start_tiles, num_start_tiles / num_tiles * 100))
    print("Goal tiles:  %d (%d/100)" % (num_goal_tiles, num_goal_tiles / num_tiles * 100))


def process_answer_set(model_str, solver, print_tiles_per_level, validate):

    # Create assignments dictionary {(tile_x, tile_y): tile_id}
    assignments_dict = Solver.get_assignments_dict(model_str)

    # Create {(tile_id, extra_info): coords} map
    tile_id_extra_info_coords_map = Solver.get_tile_id_coords_map(assignments_dict)
    if solver.save:
        tile_id_coords_maps_dir = "level_saved_files_%s/tile_id_coords_maps" % solver.player_img
        answer_set_filename = solver.get_cur_answer_set_filename()
        tile_id_coords_map_file = get_filepath(tile_id_coords_maps_dir, "%s.pickle" % answer_set_filename)
        write_pickle(tile_id_coords_map_file, tile_id_extra_info_coords_map)

    # Print num each tile type in the answer set (model_str)
    if print_tiles_per_level:
        print_num_tiles(tile_id_extra_info_coords_map, start_tile_id=solver.start_tile_id,
                        block_tile_id=solver.block_tile_id, goal_tile_id=solver.goal_tile_id)

    # Save level info to validate solution path later
    if validate:
        print("SET UP FOR SOME VALIDATING...")  # TODO validating
        # gen_level_dict[answer_set_filename] = {
        #     "tile_id_extra_info_coords_map": tile_id_extra_info_coords_map,
        #     "start_coord": solver_process.get_fact_coord(line, 'start'),
        #     "goal_coord": solver_process.get_fact_coord(line, 'goal')
        # }
        # def get_fact_coord(model_str, fact_name):
        #     facts = re.findall(r'%s\([0-9t,]*\)' % fact_name, model_str)
        #     if len(facts) == 0:
        #         error_exit("Fact '%s' not found in solver output" % fact_name)
        #     fact = facts[0]
        #     match = re.match(r'%s\((\d+),(\d+)\)' % fact_name, fact)
        #     x, y = int(match.group(1)), int(match.group(2))
        #     return x, y

    # Generate level structural txt file for the answer set
    level_structural_txt = solver.generate_level_structural_txt(assignments_dict)
    if solver.save:
        level_structural_txt_file = ""
        write_file(level_structural_txt_file, level_structural_txt)
    print(level_structural_txt)


def main(prolog_file, level_w, level_h, min_perc_blocks, start_bottom_left, max_sol,
         print_tiles_per_level, save, validate):

    # Create Solver object
    solver = Solver(prolog_file=prolog_file, level_w=level_w, level_h=level_h, min_perc_blocks=min_perc_blocks,
                    start_bottom_left=start_bottom_left, max_sol=max_sol, save=save)

    def on_model(model):
        global solver
        if solver.has_next_answer_set():
            process_answer_set(model_str=repr(model), solver=solver, print_tiles_per_level=print_tiles_per_level,
                               validate=validate)
            solver.increment_answer_set_count()
        else:
            exit(0)  # TODO END - PRINT NUM ANSWER SETS AND VALIDATE - also update for keyboard interrupt

    # Initialize tile ids in Solver object
    level_saved_files_dir = "level_saved_files_%s/" % solver.player_img
    all_prolog_info_file = get_filepath(level_saved_files_dir + "prolog_files", "all_prolog_info.pickle")
    all_prolog_info_map = read_pickle(all_prolog_info_file)
    prolog_file_info = all_prolog_info_map.get(solver.prolog_filename)
    solver.init_tile_ids(start_tile_id=prolog_file_info.get('start_tile_id'),
                         block_tile_id=prolog_file_info.get('block_tile_id'),
                         goal_tile_id=prolog_file_info.get('goal_tile_id'))

    # # Load in id_metatile map (from the metatile constraints used to create the given prolog_file)
    # id_metatile_map_file = get_filepath(level_saved_files_dir + "id_metatile_maps", "%s.pickle" % solver.prolog_filename)
    # id_metatile_map = read_pickle(id_metatile_map_file)  # TODO used for validation

    # Get temporary prolog statements based on specified options
    tmp_prolog_statements = solver.get_tmp_prolog_statements()

    # Run clingo solver
    cc = clingo.Control([])
    cc.load(solver.prolog_file)  # load statements from prolog file
    with cc.builder() as builder:
        clingo.parse_program(tmp_prolog_statements, lambda stm: builder.add(stm))  # add tmp prolog statements
    cc.add('base', [], "")
    cc.ground([('base', [])])
    cc.solve(on_model=on_model)

    # def onmodel(model):
    #     global MAX_SOL, SOLUTIONS
    #     if len(SOLUTIONS) < MAX_SOL:
    #         new_model = repr(model)
    #         SOLUTIONS.append(new_model)
    #
    #     # print(repr(m))
    #     # global MODEL_COUNT
    #     # global MAX_SOL
    #     # if MODEL_COUNT == MAX_SOL:
    #     #     exit(0)
    #     # MODEL_COUNT += 1
    #
    # files = ['tmp_prolog.pl']  # , 'level_saved_files_block/prolog_files/mario-all.pl']
    # clingo_args = []
    # clingo_control = clingo.Control(clingo_args)
    # for file in files:
    #     print("Loading file: %s ..." % file)
    #     clingo_control.load(file)
    # clingo_control.add('base', [], "")
    # clingo_control.ground([('base', [])])
    # clingo_control.solve(on_model=onmodel)

    # try:
    #     end_and_validate(tmp_prolog_file, answer_set_count, gen_level_dict, id_metatile_map, player_img, start_time)
    #
    # except KeyboardInterrupt:
    #     end_and_validate(tmp_prolog_file, answer_set_count, gen_level_dict, id_metatile_map, player_img, start_time)
    #     exit(0)


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
    parser.add_argument('--print_tiles_per_level', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--save', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--validate', const=True, nargs='?', type=bool, default=False, help="Validate generated levels")
    args = parser.parse_args()

    main(args.prolog_file, args.level_w, args.level_h, args.min_perc_blocks, args.start_bottom_left,
         args.max_sol, args.print_tiles_per_level, args.save, args.validate)

