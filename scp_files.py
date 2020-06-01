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


def get_generated_level_filepaths():

    def get_generated_level_files(prolog_file, config_file, num_sol):
        prolog_filename = get_basepath_filename(prolog_file, 'pl')
        config_filename = get_basepath_filename(config_file, 'json')
        generated_level_files = []
        for i in range(num_sol):
            generated_level_file = "%s_%s_a%d.txt" % (prolog_filename, config_filename, i)
            generated_level_files.append(generated_level_file)
        return generated_level_files

    levels = ['mario-1-1']
    max_sol = 5
    prolog_config_pairs = [
        ("level_saved_files_block/prolog_files/%s.pl", "solver_config/widths_num_tiles/config-%s-50_num_tiles.json"),
        ("level_saved_files_block/prolog_files/%s.pl", "solver_config/widths_num_tiles/config-%s-100_num_tiles.json"),
        ("level_saved_files_block/prolog_files/%s.pl", "solver_config/widths_num_tiles/config-%s-150_num_tiles.json")
    ]

    generated_level_files = []
    for level in levels:
        for prolog_file, config_file in prolog_config_pairs:
            generated_level_files += get_generated_level_files(prolog_file % level, config_file % level, max_sol)
    return ["level_structural_layers/generated/%s" % file for file in generated_level_files]


# Merge given level txt layers into single txt file
def merge_txt_files(level_filepaths, filename):
    with open(filename, 'w') as outfile:
        for filepath in level_filepaths:
            if os.path.exists(filepath):
                with open(filepath, 'r') as infile:
                    outfile.write("Level: %s\n" % filepath)
                    for line in infile:
                        outfile.write(line)
                    outfile.write("\n\n")
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
    files_transferred_count = 0
    for file in files:
        local_path = "%s" % file
        instance_path = "%s:/home/ec2-user/platformer/%s" % (INSTANCE_URL, file)
        src = local_path if push else instance_path
        dest = instance_path if push else local_path
        status = os.system("scp -i platformer.pem %s %s\n" % (src, dest))
        files_transferred_count += 1 if status == 0 else 0
    action_str = "PUSH" if push else "PULL"
    print("Files to %s: %d" % (action_str, len(files)))
    print("Files %s-ed: %d" % (action_str, files_transferred_count))


def pull_directories(dirs):
    directories_pulled = 0
    for directory in dirs:
        instance_path = "%s:/home/ec2-user/platformer/%s/" % (INSTANCE_URL, directory)
        local_path = "%s/" % directory
        status = os.system("scp -r -i platformer.pem %s %s\n" % (instance_path, local_path))
        directories_pulled += 1 if status == 0 else 0
    print("Dirs PULL-ed: %d" % directories_pulled)


def main(files, dirs, file_types, push, pull, project):

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
        files_to_transfer = files
        transfer_files(files_to_transfer, push=False, pull=True)
        pull_directories(dirs)

    # generated_level_files = get_generated_level_filepaths()
    # files_to_transfer += generated_level_files
    # merge_txt_files(generated_level_files, "combine_mario-1-1.txt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run solver and create new levels from valid answer sets')
    parser.add_argument('--files', type=str, nargs='+', help='Files to transfer', default=[])
    parser.add_argument('--dirs', type=str, nargs='+', help='Directories to transfer', default=[])
    parser.add_argument('--file_types', type=str, nargs='+', help='File types to transfer', default=FILE_TYPES)
    parser.add_argument('--push', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--pull', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--project', const=True, nargs='?', type=bool, default=False, help='Add project directories to transfer list')
    args = parser.parse_args()
    main(files=args.files, dirs=args.dirs, file_types=args.file_types, push=args.push, pull=args.pull, project=args.project)

