"""
Transfer files to or from the ec2 instance
"""

import os
import re
import argparse
from utils import error_exit

FILES = []
DIRECTORIES = []
FILE_TYPES = []

DIRECTORIES += ['', 'model', 'model_maze', 'model_platformer', 'images', 'level_structural_layers/super_mario_bros']
FILE_TYPES += ['py', 'png', 'txt', 'json']

INSTANCE_URL = "ec2-user@ec2-3-90-45-9.compute-1.amazonaws.com"

# # Pull solver generated levels from ec2 instance for specified training levels
# LEVELS = ['mario-1-1', 'mario-1-2', 'mario-1-3']
# WIDTHS = [50, 100, 150]
# MAX_SOL = 2
# for level in LEVELS:
#     for width in WIDTHS:
#         for sol in range(MAX_SOL):
#             FILES += ['level_structural_layers/generated/%s_config-%s-%d_a%d.txt' % (level, level, width, sol)]
#
# # Write solver generated levels to combined txt file
#
# with open("generated_mario_levels.txt", 'w') as outfile:
#     for file in FILES:
#         if os.path.exists(file):
#             outfile.write("Level: %s\n\n" % file)
#             with open(file, 'r') as infile:
#                 for line in infile:
#                     outfile.write(line)
#                 outfile.write("\n\n")
#
# exit(0)


def main(push, pull):

    if push == pull:
        error_exit('Push and pull are mutually exclusive')

    if not push and not pull:
        error_exit('Must specify --push or --pull')

    files_transferred_count = 0
    files_to_transfer = []

    # ----- Add all specified files -----
    files_to_transfer += FILES

    # ----- Add all files (of the specified file types) from the specified directories -----
    for directory in DIRECTORIES:
        directory_path = os.path.join(os.getcwd(), directory)
        files = os.listdir(directory_path)

        for file in files:
            for file_type in FILE_TYPES:
                if re.match(r'[a-zA-z0-9_-]+\.%s' % file_type, file) is not None:
                    files_to_transfer.append(os.path.join(directory, file))

    # ----- Transfer Files -----
    for file in files_to_transfer:
        local_path = "%s" % file
        instance_path = "%s:/home/ec2-user/platformer/%s" % (INSTANCE_URL, file)
        src = local_path if push else instance_path
        dest = instance_path if push else local_path
        transfer_status = os.system("scp -i platformer.pem %s %s\n" % (src, dest))
        files_transferred_count += 1 if transfer_status == 0 else 0

    print("Files to Transfer: %d" % len(files_to_transfer))
    print("Transferred Files: %d" % files_transferred_count)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run solver and create new levels from valid answer sets')
    parser.add_argument('--push', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--pull', const=True, nargs='?', type=bool, default=False)
    args = parser.parse_args()
    main(push=args.push, pull=args.pull)

