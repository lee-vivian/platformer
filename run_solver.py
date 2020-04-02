import subprocess
import sys
import os
import re
import argparse

import gen_prolog
import utils
from model.level import TILE_CHARS, GOAL_CHAR, START_CHAR, BLANK_CHAR


def generate_level(line, outfile, save, level_w, level_h, block_tile_id, start_tile_id, goal_tile_id):

    def get_tile_char(tile_id):
        if tile_id == block_tile_id:
            return TILE_CHARS[0]
        elif tile_id == start_tile_id:
            return START_CHAR
        elif tile_id == goal_tile_id:
            return GOAL_CHAR
        else:
            return BLANK_CHAR

    # Extract tile x, y, and id from assignment string in solver output line
    assignments = re.findall(r'assignment\([0-9t,]*\)', line)
    assignments_dict = {}  # {(tile_x, tile_y): tile_id}
    for assignment in assignments:
        match = re.match(r'assignment\((\d+),(\d+),(t\d+)\)', assignment)
        tile_x = int(match.group(1))
        tile_y = int(match.group(2))
        tile_id = match.group(3)
        assignments_dict[(tile_x, tile_y)] = tile_id

    # Generate structural txt file for new level
    level_structural_txt = ""
    for row in range(level_h):
        for col in range(level_w):
            tile_xy = (col, row)
            tile_id = assignments_dict.get(tile_xy)
            tile_char = get_tile_char(tile_id)
            level_structural_txt += tile_char
        level_structural_txt += "\n"

    # Print
    print(level_structural_txt)

    # Save structural txt file to given outfile path
    if save:
        utils.write_file(outfile, level_structural_txt)

    return True


def main(game, level, player_img, level_w, level_h, debug, max_sol, skip_print_answers, save):

    # Generate prolog file for level and return prolog dictionary
    prolog_dictionary = gen_prolog.main(game, level, player_img, level_w, level_h, debug, print_pl=False)

    # Create new directory for generated levels
    generated_levels_dir = utils.get_save_directory("generated_levels", player_img)

    # Get command to run clingo solver
    clingo_cmd = "clingo %d %s " % (max_sol, prolog_dictionary.get("filepath"))
    if skip_print_answers:
        clingo_cmd += "--quiet"

    # Track solver output
    solver_line_count = 0
    answer_set_count = 0
    answer_set_line_idx = {}

    try:
        # Run subprocess command and process each stdout line
        process = subprocess.Popen(clingo_cmd, shell=True, stdout=subprocess.PIPE)
        for line_bytes in iter(process.stdout.readline, b''):

            line = line_bytes.decode('utf-8')
            if 'Answer' in line:  # the next line contains an answer set
                answer_set_line_idx[solver_line_count+1] = 1

            if answer_set_line_idx.get(solver_line_count) is not None:  # this line contains an answer set
                answer_set_filename = "%s_a%d.txt" % (prolog_dictionary.get("filename"), answer_set_count)
                answer_set_filepath = os.path.join(generated_levels_dir, answer_set_filename)
                generate_level(line, outfile=answer_set_filepath, save=save,
                               level_w=prolog_dictionary.get("level_w"), level_h=prolog_dictionary.get("level_h"),
                               block_tile_id=prolog_dictionary.get("block_tile_id"),
                               start_tile_id=prolog_dictionary.get("start_tile_id"),
                               goal_tile_id=prolog_dictionary.get("goal_tile_id"))
                answer_set_count += 1
            solver_line_count += 1

        print("Num Levels Generated: %d" % answer_set_count)

    except KeyboardInterrupt:
        print("Num Levels Generated: %d" % answer_set_count)
        exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run solver and save valid answer sets as new levels')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--level_w', type=int, help='Number of tiles in a row', default=None)
    parser.add_argument('--level_h', type=int, help='Number of tiles in a column', default=None)
    parser.add_argument('--debug', const=True, nargs='?', type=bool, help='Allow blank tiles if no suitable assignment can be found', default=False)
    parser.add_argument('--max_sol', type=int, help='Maximum number of solutions to solve for; 0 = all', default=0)
    parser.add_argument('--skip_print_answers', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--save', const=True, nargs='?', type=bool, default=False)

    args = parser.parse_args()
    main(args.game, args.level, args.player_img, args.level_w, args.level_h,
         args.debug, args.max_sol, args.skip_print_answers, args.save)
