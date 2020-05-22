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

DIRECTORIES += ['', 'model', 'model_maze', 'model_platformer', 'images']
FILE_TYPES += ['py', 'png']

INSTANCE_URL = "ec2-user@ec2-100-24-26-91.compute-1.amazonaws.com"


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
        os.system("scp -i platformer.pem %s %s\n" % (src, dest))
        files_transferred_count += 1

    print("Transfered Files: %d" % files_transferred_count)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run solver and create new levels from valid answer sets')
    parser.add_argument('--push', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--pull', const=True, nargs='?', type=bool, default=False)
    args = parser.parse_args()
    main(push=args.push, pull=args.pull)

