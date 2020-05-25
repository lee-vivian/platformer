"""
Returns a map of the states associated with each metatile for a given level {metatile_str : {state_coord: 1}}
"""

import argparse
import networkx as nx
from datetime import datetime

from utils import read_pickle, write_pickle, get_filepath


def get_metatile_num_states_stats(metatile_num_states_dict):
    total_metatile_count = 0
    total_state_count = 0
    max_states_per_metatile = 0

    for metatile, num_states in metatile_num_states_dict.items():
        total_metatile_count += 1
        total_state_count += num_states
        max_states_per_metatile = max(max_states_per_metatile, num_states)

    stats = "Num metatiles: %d\n" % total_metatile_count
    stats += "Num states: %d\n" % total_state_count
    stats += "Max states per metatile: %d\n" % max_states_per_metatile
    stats += "Avg states per metatile: %d\n" % int(total_state_count / total_metatile_count)
    return stats


def main(save_filename, unique_metatiles_file, player_img, print_stats):

    print("Calculating states per metatile stats for the given unique_metatiles_file: %s" % unique_metatiles_file)
    start_time = datetime.now()

    save_directory = "level_saved_files_%s/metatile_num_states_dicts/" % player_img
    save_file = "%s.pickle" % save_filename
    metatile_num_states_dict_file = get_filepath(save_directory, save_file)

    unique_metatiles = read_pickle(unique_metatiles_file)
    metatile_num_states_dict = {}

    for metatile in unique_metatiles:
        metatile_str = metatile.to_str()
        metatile_graph = nx.DiGraph(metatile.graph_as_dict)
        num_states = len(metatile_graph.nodes())
        metatile_num_states_dict[metatile_str] = num_states

    write_pickle(metatile_num_states_dict_file, metatile_num_states_dict)

    end_time = datetime.now()
    runtime = str(end_time-start_time)

    if print_stats:
        print(get_metatile_num_states_stats(metatile_num_states_dict))

    print("Runtime: %s\n" % runtime)

    return runtime


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get number of states per metatile from the unique_metatiles file')
    parser.add_argument('save_filename', type=str, help='File name to save extracted info to')
    parser.add_argument('unique_metatiles_file', type=str, help='File path of the unique_metatiles file to use')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--print_stats', const=True, nargs='?', type=bool, default=False)
    args = parser.parse_args()

    main(args.save_filename, args.unique_metatiles_file, args.player_img, args.print_stats)
