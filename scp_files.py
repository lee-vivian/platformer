"""
Transfer files to or from the ec2 instance
"""

import os
import re
import argparse
from utils import error_exit, get_basepath_filename

INSTANCE_URL = "ec2-user@ec2-3-90-45-9.compute-1.amazonaws.com"

FILE_TYPES = ['py', 'png', 'txt', 'json']

PROJECT_DIRS = ['', 'model', 'model_maze', 'model_platformer', 'images', 'level_structural_layers/super_mario_bros',
                'solver_config', 'solver_config/widths_num_tiles']

VALIDATE_ASP_DIRS = ['level_saved_files_block/generated_level_model_strs']
VALIDATE_GRAPH_DIRS = ['level_saved_files_block/generated_level_assignments_dicts',
                       'level_saved_files_block/id_metatile_maps']

LEVELS = ['mario-1-1', 'mario-1-2', 'mario-1-3']
MAX_SOL = 5
PROLOG_CONFIG_PAIRS = [
    ("level_saved_files_block/prolog_files/%s.pl", "solver_config/widths_num_tiles/config-%s-50_num_tiles.json"),
    ("level_saved_files_block/prolog_files/%s.pl", "solver_config/widths_num_tiles/config-%s-100_num_tiles.json"),
    ("level_saved_files_block/prolog_files/%s.pl", "solver_config/widths_num_tiles/config-%s-150_num_tiles.json")
]


def get_generated_level_filepaths(levels, max_sol, prolog_config_pairs):

    generated_level_filepaths = []
    generated_level_filepath_format = "level_structural_layers/generated/%s.txt"

    for level in levels:
        for prolog_file_format, config_file_format in prolog_config_pairs:

            prolog_filename = get_basepath_filename(prolog_file_format % level, 'pl')
            config_filename = get_basepath_filename(config_file_format % level, 'json')
            answer_set_file_format = "%s_%s_" % (prolog_filename, config_filename) + "a%d"

            for sol in range(max_sol):
                generated_level_filepaths.append(generated_level_filepath_format % (answer_set_file_format % sol))

    return generated_level_filepaths


# Merge given level txt layers into single txt file
def merge_txt_files(level_filepaths, filename):
    count = 0
    with open(filename, 'w') as outfile:
        for filepath in level_filepaths:
            if os.path.exists(filepath):
                count += 1
                with open(filepath, 'r') as infile:
                    outfile.write("Level: %s\n" % filepath)
                    for line in infile:
                        outfile.write(line)
                    outfile.write("\n\n")
        outfile.write("\nCombined Levels: %d\n" % count)
    print("Saved to: %s" % filename)


def get_local_files_to_transfer(files, dirs, file_types):
    files_to_transfer = []

    # ----- Add all specified files -----
    files_to_transfer += files

    # ----- Add all files (of the specified file types) from the specified directories -----
    for directory in dirs:
        directory_path = os.path.join(os.getcwd(), directory)
        files_in_dir = os.listdir(directory_path)
        for file in files_in_dir:
            for file_type in file_types:
                if re.match(r'[a-zA-z0-9_-]+\.%s' % file_type, file) is not None:
                    filepath = os.path.join(directory, file)
                    files_to_transfer.append(filepath)

    return files_to_transfer


def transfer_files(files, push, pull):
    success_files = []
    failed_files = []
    for file in files:
        local_path = "%s" % file
        instance_path = "%s:/home/ec2-user/platformer/%s" % (INSTANCE_URL, file)
        src = local_path if push else instance_path
        dest = instance_path if push else local_path
        status = os.system("scp -i platformer.pem %s %s\n" % (src, dest))
        if status == 0:
            success_files.append(file)
        else:
            failed_files.append(file)

    action_str = "PUSH" if push else "PULL"
    print("Files to %s: %d" % (action_str, len(files)))
    print("Files %s-ed: %d" % (action_str, len(success_files)))
    print("Files not %s-ed: %d" % (action_str, len(failed_files)))

    return success_files, failed_files


def pull_directories(dirs):
    directories_pulled = 0
    for directory in dirs:
        instance_path = "%s:/home/ec2-user/platformer/%s/" % (INSTANCE_URL, directory)
        local_path = "%s/" % directory
        status = os.system("scp -r -i platformer.pem %s %s\n" % (instance_path, local_path))
        directories_pulled += 1 if status == 0 else 0
    print("Dirs PULL-ed: %d" % directories_pulled)


def main(files, dirs, file_types, push, pull, project, gen_levels, validate_asp, validate_graph):

    if push == pull:
        error_exit('Push and pull are mutually exclusive')

    if not push and not pull:
        error_exit('Must specify --push or --pull')

    if push:
        if project:
            dirs += PROJECT_DIRS
        files_to_transfer = get_local_files_to_transfer(files, dirs, file_types)
        transfer_files(files_to_transfer, push=True, pull=False)

    if pull:
        if gen_levels:
            files_to_transfer = get_generated_level_filepaths(LEVELS, MAX_SOL, PROLOG_CONFIG_PAIRS)
            success_files, failed_files = transfer_files(files_to_transfer, push=False, pull=True)
            merge_txt_files(success_files, 'combined_generated_levels.txt')

        if validate_asp:
            pull_directories(VALIDATE_ASP_DIRS)

        if validate_graph:
            pull_directories(VALIDATE_GRAPH_DIRS)

        files_to_transfer = files
        transfer_files(files_to_transfer, push=False, pull=True)
        pull_directories(dirs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run solver and create new levels from valid answer sets')
    parser.add_argument('--files', type=str, nargs='+', help='Files to transfer', default=[])
    parser.add_argument('--dirs', type=str, nargs='+', help='Directories to transfer', default=[])
    parser.add_argument('--file_types', type=str, nargs='+', help='File types to transfer', default=FILE_TYPES)
    parser.add_argument('--push', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--pull', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--project', const=True, nargs='?', type=bool, default=False, help='Add project directories to push transfer list')
    parser.add_argument('--gen_levels', const=True, nargs='?', type=bool, default=False, help='Add generated level files to pull transfer list')
    parser.add_argument('--validate_asp', const=True, nargs='?', type=bool, default=False, help='Add validate asp directories to pull transfer list')
    parser.add_argument('--validate_graph', const=True, nargs='?', type=bool, default=False, help='Add validate state graph directories to pull transfer list')
    args = parser.parse_args()
    main(files=args.files, dirs=args.dirs, file_types=args.file_types, push=args.push, pull=args.pull,
         project=args.project, gen_levels=args.gen_levels, validate_asp=args.validate_asp, validate_graph=args.validate_graph)

