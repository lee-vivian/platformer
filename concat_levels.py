'''
Concat level structural txt files
'''

import argparse

from utils import all_equal, error_exit, write_file, get_directory


def main(new_filepath, files):

    level_num_lines_dict = {}  # {level_idx: num lines}
    level_lines_dict = {}  # {level_idx: list-of-lines}

    for level_idx in range(len(files)):  # for each level file
        filepath = files[level_idx]
        level_num_lines_dict[level_idx] = 0
        level_lines_dict[level_idx] = []

        f = open(filepath, 'r')  # iterate through each line of the level file
        for line in f:
            level_num_lines_dict[level_idx] += 1  # add level line count
            level_lines_dict[level_idx].append(line.rstrip())  # add level lines

    same_height_for_all_levels = all_equal(list(level_num_lines_dict.values()))
    if not same_height_for_all_levels:
        error_exit("Level heights are not the same for all levels")

    concat_level_txt = ""

    for line_idx in range(len(level_lines_dict[0])):  # for each line in a level
        cur_line = ""
        for level_idx in range(len(level_lines_dict)):  # for each level
            cur_line += level_lines_dict[level_idx][line_idx]
        concat_level_txt += cur_line + "\n"

    write_file(new_filepath, concat_level_txt)

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Concat level structural txt files')
    parser.add_argument('new_filepath', type=str, help='Full filepath of the new concatenated level')
    parser.add_argument('files', type=str, nargs='+', help='Files to concat')
    args = parser.parse_args()
    main(args.new_filepath, args.files)
