import subprocess
import os
import re
import argparse
from datetime import datetime

import clingo

MODEL_COUNT = 0
MAX_SOL = 1

# TODO test with sample_mini
# update tmp_prolog to return str of prolog statements not create/delete file
# read in pl file
# remove duplicate lines
# add unique statements to clingo_control
# solve

# update args and make this part functions
# handle UNSAT and parsing valid solutions

files = ['tmp_prolog.pl', 'level_saved_files_block/prolog_files/sample_mini.pl']  #, 'level_saved_files_block/prolog_files/mario-all.pl']
clingo_args = []
clingo_control = clingo.Control(clingo_args)
for file in files:
    print("Loading file: %s ..." % file)
    clingo_control.load(file)
clingo_control.add('base', [], "")
clingo_control.ground([('base', [])])


def onmodel(m):
    print(repr(m))
    # global MODEL_COUNT
    # global MAX_SOL
    # if MODEL_COUNT == MAX_SOL:
    #     exit(0)
    # MODEL_COUNT += 1


def add_pl_statements(clingo_control, statements):
    with clingo_control.builder() as builder:
        clingo.parse_program(statements, lambda stm: builder.add(stm))


print((clingo_control.solve(on_model=onmodel)))


exit(0)



import get_metatile_id_map
import solver_process, solver_validate
from utils import get_directory, read_pickle, write_file, get_filepath


def parse_prolog_filepath(prolog_filepath):
    match = re.match('level_saved_files_([^/]+)/prolog_files/([a-zA-Z0-9_-]+).pl', prolog_filepath)
    player_img = match.group(1)
    prolog_filename = match.group(2)
    return player_img, prolog_filename


def create_temporary_prolog_file(level_w, level_h, min_perc_blocks, start_bottom_left, start_tile_id, block_tile_id):
    print("Creating temporary prolog file with specified options...")
    print("-- level dimensions in tiles: (%d, %d)" % (level_w, level_h))
    print("-- minimum percentage of block tiles: %s" % str(min_perc_blocks))
    print("-- start tile fixed to bottom left: %s" % str(start_bottom_left))

    tmp_prolog_statements = ""
    tmp_prolog_statements += "dim_width(0..%d).\n" % (level_w - 1)
    tmp_prolog_statements += "dim_height(0..%d).\n" % (level_h - 1)

    # Create tile facts
    create_tiles_statement = "tile(TX,TY) :- dim_width(TX), dim_height(TY)."
    tmp_prolog_statements += create_tiles_statement + "\n"

    # Set border tiles to be block tiles
    block_tile_coords = []
    for x in range(level_w):
        block_tile_coords += [(x, 0), (x, level_h - 1)]
    for y in range(level_h):
        block_tile_coords += [(0, y), (level_w - 1, y)]
    for x, y in list(set(block_tile_coords)):
        block_tile_assignment = "assignment(%d, %d, %s)." % (x, y, block_tile_id)
        tmp_prolog_statements += block_tile_assignment + "\n"

    # Fix start tile to bottom left of the generated level
    if start_bottom_left:
        start_tile_assignment = "assignment(%d, %d, %s)." % (1, level_h - 2, start_tile_id)
        tmp_prolog_statements += start_tile_assignment + "\n"

    # Set minimum percentage of block tiles allowed in generated level
    if min_perc_blocks is not None:
        # Limit number of block tiles
        total_tiles = int(level_w * level_h)
        min_perc_blocks_statement = "limit(%s, %d, %d)." % (
        block_tile_id, int(min_perc_blocks / 100 * total_tiles), total_tiles)
        tmp_prolog_statements += min_perc_blocks_statement + "\n"

    # Save temporary prolog file
    tmp_prolog_file = "tmp_prolog.pl"
    write_file(tmp_prolog_file, tmp_prolog_statements)

    return tmp_prolog_file


def print_num_tiles(tile_id_extra_info_coords_map, block_tile_id, start_tile_id, goal_tile_id):
    num_tiles, num_block_tiles, num_start_tiles, num_goal_tiles = 0, 0, 0, 0

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


def end_and_validate(tmp_prolog_file, answer_set_count, gen_level_dict, id_metatile_map, player_img, start_time):
    os.remove(tmp_prolog_file)  # delete temporary prolog file

    print("Num Levels Generated: %d" % answer_set_count)

    if gen_level_dict is not None:
        solver_validate.main(gen_level_dict, id_metatile_map, player_img)

    end_time = datetime.now()
    print("Total Runtime: %s" % str(end_time-start_time))


def main(prolog_file, level_w, level_h, min_perc_blocks, start_bottom_left, max_sol, skip_print_answers,
         print_tiles_per_level, save, validate):
    # Parse prolog filepath
    player_img, prolog_filename = parse_prolog_filepath(prolog_file)

    # Get prolog file info
    level_saved_files_dir = "level_saved_files_%s/" % player_img
    all_prolog_info_filepath = get_filepath(level_saved_files_dir + "prolog_files", "all_prolog_info.pickle")
    all_prolog_info_map = read_pickle(all_prolog_info_filepath)
    prolog_file_info = all_prolog_info_map.get(prolog_filename)

    # Load in id_metatile map from the metatile constraints used to create the given prolog_file
    id_metatile_map_file = get_filepath(level_saved_files_dir + "id_metatile_maps", "%s.pickle" % prolog_filename)
    id_metatile_map = read_pickle(id_metatile_map_file)

    # Create temporary prolog file
    tmp_prolog_file = create_temporary_prolog_file(level_w, level_h, min_perc_blocks, start_bottom_left,
                                                   start_tile_id=prolog_file_info.get("start_tile_id"),
                                                   block_tile_id=prolog_file_info.get("block_tile_id"))

    # Construct command to run clingo solver
    clingo_cmd = "clingo %d %s %s" % (max_sol, prolog_file, tmp_prolog_file)
    if skip_print_answers:
        clingo_cmd += "--quiet"

    # Create new directory for generated levels
    generated_levels_dir = get_directory("level_structural_layers/generated")

    # Track solver output
    solver_line_count = 0
    answer_set_count = 0
    answer_set_line_idx = {}

    # Track to validate level solution paths later
    if validate:
        gen_level_dict = {}
    else:
        gen_level_dict = None

    print("Running clingo solver: %s" % clingo_cmd)
    start_time = datetime.now()

    try:
        # Run subprocess command and process each stdout line
        process = subprocess.Popen(clingo_cmd, shell=True, stdout=subprocess.PIPE)
        for line_bytes in iter(process.stdout.readline, b''):

            line = line_bytes.decode('utf-8')
            if 'Answer' in line:  # the next line contains an answer set
                answer_set_line_idx[solver_line_count + 1] = 1

            if answer_set_line_idx.get(solver_line_count) is not None:  # this line contains an answer set
                answer_set_filename = "%s_w%d_h%d_a%d" % (prolog_filename, level_w, level_h, answer_set_count)
                answer_set_filepath = os.path.join(generated_levels_dir, answer_set_filename + ".txt")
                assignments_dict = solver_process.get_assignments_dict(line)  # {(tile_x, tile_y): tile_id}

                # Create {(tile_id, extra_info): coords} map (used to draw metatile labels)
                tile_id_extra_info_coords_map = solver_process.create_tile_id_coords_map(assignments_dict,
                                                                                         answer_set_filename,
                                                                                         player_img, save=save)
                if print_tiles_per_level:
                    print_num_tiles(tile_id_extra_info_coords_map,
                                    block_tile_id=prolog_file_info.get("block_tile_id"),
                                    start_tile_id=prolog_file_info.get("start_tile_id"),
                                    goal_tile_id=prolog_file_info.get("goal_tile_id"))

                # Save level info to validate solution path later
                if validate:
                    gen_level_dict[answer_set_filename] = {
                        "tile_id_extra_info_coords_map": tile_id_extra_info_coords_map,
                        "start_coord": solver_process.get_fact_coord(line, 'start'),
                        "goal_coord": solver_process.get_fact_coord(line, 'goal')
                    }

                # Create level structural txt file for the answer set
                solver_process.generate_level(assignments_dict, level_w=level_w, level_h=level_h,
                                              block_tile_id=prolog_file_info.get("block_tile_id"),
                                              start_tile_id=prolog_file_info.get("start_tile_id"),
                                              goal_tile_id=prolog_file_info.get("goal_tile_id"),
                                              outfile=answer_set_filepath, save=save)
                answer_set_count += 1

            solver_line_count += 1

        end_and_validate(tmp_prolog_file, answer_set_count, gen_level_dict, id_metatile_map, player_img, start_time)

    except KeyboardInterrupt:

        end_and_validate(tmp_prolog_file, answer_set_count, gen_level_dict, id_metatile_map, player_img, start_time)
        exit(0)


if __name__ == "__main__":

    main('level_saved_files_block/prolog_files/mario-all.pl', level_w=50, level_h=6, min_perc_blocks=None,
         start_bottom_left=True, max_sol=2, skip_print_answers=False, print_tiles_per_level=True, save=True,
         validate=True)

    main('level_saved_files_block/prolog_files/mario-all.pl', level_w=50, level_h=6, min_perc_blocks=65,
         start_bottom_left=True, max_sol=2, skip_print_answers=False, print_tiles_per_level=True, save=True,
         validate=True)

    # main('level_saved_files_block/prolog_files/mario-icarus-1.pl', level_w=30, level_h=6, min_perc_blocks=None,
    #      start_bottom_left=True, max_sol=2, skip_print_answers=False, print_tiles_per_level=True, save=True,
    #      validate=True)
    #
    # main('level_saved_files_block/prolog_files/mario-icarus-1.pl', level_w=18, level_h=100, min_perc_blocks=None,
    #      start_bottom_left=True, max_sol=2, skip_print_answers=False, print_tiles_per_level=True, save=True,
    #      validate=True)

    exit(0)


    parser = argparse.ArgumentParser(description='Run solver and create new levels from valid answer sets')
    parser.add_argument('prolog_file', type=str, help="File path of the prolog file to use")
    parser.add_argument('level_w', type=int, help="Number of tiles in a row")
    parser.add_argument('level_h', type=int, help="Number of tiles in a column")
    parser.add_argument('--min_perc_blocks', type=int, default=None, help='Minimum percentage of block tiles in a level')
    parser.add_argument('--start_bottom_left', const=True, nargs='?', type=bool, default=False, help='Fix start position to the bottom left of the level')
    parser.add_argument('--max_sol', type=int, default=0, help="Max number of answer sets to return; 0 = all")
    parser.add_argument('--skip_print_answers', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--print_tiles_per_level', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--save', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--validate', const=True, nargs='?', type=bool, default=False, help="Validate generated levels")
    args = parser.parse_args()

    main(args.prolog_file, args.level_w, args.level_h, args.min_perc_blocks, args.start_bottom_left,
         args.max_sol, args.skip_print_answers, args.print_tiles_per_level, args.save, args.validate)

