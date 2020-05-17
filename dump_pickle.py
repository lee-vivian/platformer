"""
Dump info about the precomputed state graph.
"""

import argparse
import pickle
import pprint

def main(pickle_file):
    with (open(pickle_file, "rb")) as openfile:
        while True:
            try:
                pprint.pprint(pickle.load(openfile))
            except EOFError:
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Print pickle file')
    parser.add_argument('pickle_file', type=str, help="File path to print")
    args = parser.parse_args()

    main(args.pickle_file)
