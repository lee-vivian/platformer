import subprocess
import os
import argparse
from datetime import datetime

import get_metatile_id_map
import gen_prolog, solver_process, solver_validate
import utils


def main(game, level, player_img, level_w, level_h, min_perc_blocks, debug, max_sol, skip_print_answers,
         print_tiles_per_level, save, validate):

    # Generate prolog file for level and return prolog dictionary
    prolog_dictionary = gen_prolog.main(game, level, player_img, level_w, level_h, debug,
                                        print_pl=False, min_perc_blocks=min_perc_blocks)

    # Get id_metatile map for level
    id_metatile_map = get_metatile_id_map.main([game], [level], player_img, outfile=None,
                                               save=False).get("id_metatile_map")

    # Create new directory for generated levels
    generated_levels_dir = utils.get_directory("level_structural_layers/generated")

    # Get command to run clingo solver
    clingo_cmd = "clingo %d %s " % (max_sol, prolog_dictionary.get("filepath"))
    if skip_print_answers:
        clingo_cmd += "--quiet"

    # Track solver output
    solver_line_count = 0
    answer_set_count = 0
    answer_set_line_idx = {}

    # Track to validate level solution paths later
    if validate:
        gen_level_dict = {}

    print("Running: %s" % clingo_cmd)
    start = datetime.now()

    try:
        # Run subprocess command and process each stdout line
        process = subprocess.Popen(clingo_cmd, shell=True, stdout=subprocess.PIPE)
        for line_bytes in iter(process.stdout.readline, b''):

            line = line_bytes.decode('utf-8')
            if 'Answer' in line:  # the next line contains an answer set
                answer_set_line_idx[solver_line_count+1] = 1

            if answer_set_line_idx.get(solver_line_count) is not None:  # this line contains an answer set

                answer_set_filename = "%s_a%d" % (prolog_dictionary.get("filename"), answer_set_count)
                answer_set_filepath = os.path.join(generated_levels_dir, answer_set_filename + ".txt")
                assignments_dict = solver_process.get_assignments_dict(line)  # {(tile_x, tile_y): tile_id}

                # Used to draw metatile labels
                tile_id_extra_info_coords_map = solver_process.create_tile_id_coords_map(assignments_dict, answer_set_filename,
                                                                          player_img, save=save)

                if print_tiles_per_level:
                    print_num_tiles(tile_id_extra_info_coords_map,
                                    block_tile_id=prolog_dictionary.get("block_tile_id"),
                                    start_tile_id=prolog_dictionary.get("start_tile_id"),
                                    goal_tile_id=prolog_dictionary.get("goal_tile_id"))

                # Save level info to validate solution path later
                if validate:
                    gen_level_dict[answer_set_filename] = {
                        "tile_id_extra_info_coords_map": tile_id_extra_info_coords_map,
                        "start_coord": solver_process.get_fact_coord(line, 'start'),
                        "goal_coord": solver_process.get_fact_coord(line, 'goal')
                    }

                # create level structural txt file for the answer set
                solver_process.generate_level(assignments_dict,
                                              level_w=prolog_dictionary.get("level_w"),
                                              level_h=prolog_dictionary.get("level_h"),
                                              block_tile_id=prolog_dictionary.get("block_tile_id"),
                                              start_tile_id=prolog_dictionary.get("start_tile_id"),
                                              goal_tile_id=prolog_dictionary.get("goal_tile_id"),
                                              outfile=answer_set_filepath, save=save)
                answer_set_count += 1

            solver_line_count += 1

        print("Num Levels Generated: %d" % answer_set_count)
        if validate:
            solver_validate.main(gen_level_dict, id_metatile_map, player_img)
        end = datetime.now()
        print("Total Runtime %s" % str(end-start))

    except KeyboardInterrupt:
        print("Num Levels Generated: %d" % answer_set_count)
        if validate:
            solver_validate.main(gen_level_dict, id_metatile_map, player_img)
        end = datetime.now()
        print("Total Runtime %s" % str(end - start))
        exit(0)


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run solver and save valid answer sets as new levels')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--level_w', type=int, help='Number of tiles in a row', default=None)
    parser.add_argument('--level_h', type=int, help='Number of tiles in a column', default=None)
    parser.add_argument('--min_perc_blocks', type=int, help='Percent number of block tiles in a level', default=None)
    parser.add_argument('--debug', const=True, nargs='?', type=bool, help='Allow blank tiles if no suitable assignment can be found', default=False)
    parser.add_argument('--max_sol', type=int, help='Maximum number of solutions to solve for; 0 = all', default=0)
    parser.add_argument('--skip_print_answers', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--print_tiles_per_level', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--save', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--validate', const=True, nargs='?', type=bool, default=False)

    args = parser.parse_args()
    main(args.game, args.level, args.player_img, args.level_w, args.level_h,
         args.min_perc_blocks, args.debug, args.max_sol, args.skip_print_answers,
         args.print_tiles_per_level, args.save, args.validate)