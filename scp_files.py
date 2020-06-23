"""
Transfer files to or from the ec2 instance
"""

import os
import argparse

from utils import error_exit, get_directory, get_filepath

INSTANCE_URL = "ec2-user@ec2-3-92-138-153.compute-1.amazonaws.com"
PEM_FILEPATH = "platformer.pem"

PROJECT_FILE_TYPES = ['py', 'png', 'txt', 'json']

PROJECT_DIRS = ['', 'model', 'model_maze', 'model_platformer', 'images', 'level_structural_layers/super_mario_bros',
                'solver_config', 'solver_config/widths_num_tiles', 'solver_config/controllability']

TRIAL_DIRS = ['level_structural_layers/generated',
              'solver_console_output',
              'level_saved_files_block/generated_level_model_strs',
              'level_saved_files_block/generated_level_assignments_dicts',
              'level_saved_files_block/id_metatile_maps']


def get_processed_level_files(player_img, game, levels):
    processed_files = ['all_levels_process_info.pickle', 'level_saved_files_%s/prolog_files/all_prolog_info.pickle' % player_img]
    for level in levels:
        processed_files += [
            'process_console_output/%s.txt' % level,
            'level_saved_files_%s/enumerated_state_graphs/%s/%s.gpickle' % (player_img, game, level),
            'level_saved_files_%s/unique_metatiles/%s.pickle' % (player_img, level),
            'level_saved_files_%s/metatile_coords_dicts/%s/%s.pickle' % (player_img, game, level),
            'level_saved_files_%s/id_metatile_maps/%s.pickle' % (player_img, level),
            'level_saved_files_%s/metatile_id_maps/%s.pickle' % (player_img, level),
            'level_saved_files_%s/tile_id_coords_maps/%s/%s.pickle' % (player_img, game, level),
            'level_saved_files_%s/metatile_num_states_dicts/%s.pickle' % (player_img, level),
            'level_saved_files_%s/metatile_constraints/%s.pickle' % (player_img, level),
            'level_saved_files_%s/prolog_files/%s.pl' % (player_img, level)]
    return processed_files


def get_files_to_transfer(files, dirs, file_types):
    files_to_transfer = []
    files_to_transfer += files
    for directory in dirs:
        directory_path = os.path.join(os.getcwd(), directory)
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            if os.path.isfile(item_path) and item.endswith(tuple(file_types)):
                files_to_transfer.append(os.path.join(directory, item))

    return files_to_transfer


def transfer_files(files, push):
    success_files = []
    failed_files = []

    for file in files:
        local_path = file
        instance_path = "%s:/home/ec2-user/platformer/%s" % (INSTANCE_URL, file)
        src = local_path if push else instance_path
        dest = instance_path if push else local_path
        status = os.system("scp -i %s %s %s\n" % (PEM_FILEPATH, src, dest))
        if status == 0:
            success_files.append(file)
        else:
            failed_files.append(file)

    action = "PUSH" if push else "PULL"
    print("Files to %s: %d" % (action, len(files)))
    print("Success: %d" % len(success_files))
    print("Failed: %d" % len(failed_files))

    return success_files, failed_files


def pull_directories(dirs):
    directories_pulled = 0
    for directory in dirs:
        instance_path = "%s:/home/ec2-user/platformer/%s/." % (INSTANCE_URL, directory)
        local_path = get_directory(directory)
        status = os.system("scp -r -i %s %s %s\n" % (PEM_FILEPATH, instance_path, local_path))
        directories_pulled += 1 if status == 0 else 0
    print("Directories Pulled: %d" % directories_pulled)


def main(push, pull, files, dirs, file_types, push_project, pull_trials, pull_processed):

    if not any([push, pull, push_project, pull_trials, pull_processed]):
        error_exit("Must specify a push/pull action. View options with python scp_files.py --help")

    if push_project:
        files_to_transfer = get_files_to_transfer(files=[], dirs=PROJECT_DIRS, file_types=PROJECT_FILE_TYPES)
        transfer_files(files_to_transfer, push=True)
        return

    if pull_trials:
        pull_directories(dirs=TRIAL_DIRS)
        return

    if pull_processed is not None:
        if len(pull_processed) <= 1:
            error_exit('--pull_processed args should be in the format <game> <level1> <level2> ...')
        else:
            files_to_transfer = get_processed_level_files(player_img='block', game=pull_processed[0],
                                                          levels=pull_processed[1:])
            for file in files_to_transfer:
                get_filepath(os.path.dirname(file), os.path.basename(file))
            transfer_files(files_to_transfer, push=False)

    if push and pull:
        error_exit('Push and pull are mutually exclusive')

    files_to_transfer = get_files_to_transfer(files=files, dirs=dirs, file_types=file_types)
    transfer_files(files_to_transfer, push=push)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run solver and create new levels from valid answer sets')
    parser.add_argument('--push', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--pull', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--files', type=str, nargs='+', help='Files to transfer', default=[])
    parser.add_argument('--dirs', type=str, nargs='+', help='Directories to transfer', default=[])
    parser.add_argument('--file_types', type=str, nargs='+', help='File types to transfer', default=PROJECT_FILE_TYPES)
    parser.add_argument('--push_project', const=True, nargs='?', type=bool, default=False, help='Push project files to instance')
    parser.add_argument('--pull_trials', const=True, nargs='?', type=bool, default=False, help='Pull generated level files from trials'),
    parser.add_argument('--pull_processed', type=str, nargs='+', help='Pull processed level files, format = <game> <level1> <level2>...')
    args = parser.parse_args()
    main(push=args.push, pull=args.pull, files=args.files, dirs=args.dirs, file_types=args.file_types,
         push_project=args.push_project, pull_trials=args.pull_trials, pull_processed=args.pull_processed)

