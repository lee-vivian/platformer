import os
import re
import argparse

import gen_prolog
import utils


def generate_level(line, answer_set_filepath):

    assignments = re.findall(r'assignment\([0-9t,]*\)', line)
    for x in assignments:
        print(x)


    return True


def main(game, level, player_img, level_w, level_h, debug, max_sol, skip_print_answers):

    # Generate prolog file for level and return file path
    prolog_filename, prolog_filepath = gen_prolog.main(game, level, player_img, level_w, level_h, debug, print_pl=False)

    # Create new directory for generated levels
    generated_levels_dir = utils.get_save_directory("generated_levels", player_img)

    # Get command to run clingo solver
    clingo_cmd = "clingo %d %s " % (max_sol, prolog_filepath)
    if skip_print_answers:
        clingo_cmd += "--quiet"

    # Read solver output
    clingo_output = os.popen(clingo_cmd).read()

    # Parse solver output and generate new levels from valid answer sets
    solver_line_count = 0
    answer_set_count = 0
    answer_set_line_idx = {}

    for line in clingo_output.splitlines():  # for each line in the solver output

        if re.search(r'Answer', line) is not None:
            answer_set_line_idx[solver_line_count+1] = 1  # the next line contains an answer set

        if answer_set_line_idx.get(solver_line_count) is not None:  # this line contains an answer set

            answer_set_filename = "%s_a%d.txt" % (prolog_filename, answer_set_count)
            answer_set_filepath = os.path.join(generated_levels_dir, answer_set_filename)
            generate_level(line, answer_set_filepath)
            answer_set_count += 1

        solver_line_count += 1

    print("Num Levels Generated: %d" % answer_set_count)


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

    args = parser.parse_args()
    main(args.game, args.level, args.player_img, args.level_w, args.level_h, args.debug, args.max_sol, args.skip_print_answers)

