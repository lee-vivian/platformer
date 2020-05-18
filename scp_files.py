"""
Transfer files to or from the ec2 instance
"""

import argparse
from utils import error_exit

GAME_LEVEL_PAIRS = [
    ('super_mario_bros', 'mario-1-1'),
    ('super_mario_bros', 'mario-1-2'),
    ('kid_icarus', 'kidicarus_1')
]

FILES = []


def main(push, pull):

    if push == pull:
        error_exit('Push and pull are mutually exclusive')

    if not push and not pull:
        error_exit('Must specify --push or --pull')

    # ----- Add Processed Level Files -----

    filepaths = []

    for game, level in GAME_LEVEL_PAIRS:
        filepaths.append('level_saved_files_block/enumerated_state_graphs/%s/%s.gpickle' % (game, level))
        filepaths.append('level_saved_files_block/unique_metatiles/%s.pickle' % level)
        filepaths.append('level_saved_files_block/metatile_coords_dicts/%s/%s.pickle' % (game, level))
        filepaths.append('level_saved_files_block/id_metatile_maps/%s.pickle' % level)
        filepaths.append('level_saved_files_block/metatile_id_maps/%s.pickle' % level)
        filepaths.append('level_saved_files_block/tile_id_coords_maps/%s/%s.pickle' % (game, level))
        filepaths.append('level_saved_files_block/metatile_num_states_dicts/%s.pickle' % level)
        filepaths.append('level_saved_files_block/metatile_constraints/%s.pickle' % level)
        filepaths.append('level_saved_files_block/prolog_files/%s.pl' % level)
        filepaths.append('level_saved_files_block/prolog_files/all_prolog_info.pickle')

    # ----- Add Other Specified Files -----

    filepaths += FILES
    filepaths = list(set(filepaths))
    count = 0

    # ----- Transfer Files -----

    for filepath in filepaths:
        local_path = "%s" % filepath
        instance_path = "ec2-user@ec2-34-229-80-241.compute-1.amazonaws.com:/home/ec2-user/platformer/%s" % filepath

        if push:
            transfer_str = "scp -i platformer.pem %s %s\n" % (local_path, instance_path)
        elif pull:
            transfer_str = "scp -i platformer.pem %s %s\n" % (instance_path, local_path)
        else:
            transfer_str = ""

        print(transfer_str)
        count += 1

    print("total files: %d" % count)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run solver and create new levels from valid answer sets')
    parser.add_argument('--push', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--pull', const=True, nargs='?', type=bool, default=False)
    args = parser.parse_args()
    main(push=args.push, pull=args.pull)

