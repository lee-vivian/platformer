'''
Returns a map of the number of states associated with each metatile for a given level {metatile_str : num states}
'''

import argparse
import networkx as nx
import os
import pickle
import json

from model.metatile import Metatile


def error_exit(msg):
    print(msg)
    exit(0)


def write_json(filepath, contents):
    with open(filepath, 'w') as file:
        json.dump(contents, file, indent=2, sort_keys=True)
    file.close()
    print("Saved to:", filepath)
    return filepath


def read_pickle(filepath):
    with open(filepath, 'rb') as file:
        contents = pickle.load(file)
    file.close()
    return contents


def get_state_graph(game, level, player_img):
    game_enumerated_state_graph_dir = "level_saved_files_%s/enumerated_state_graphs/%s/" % (player_img, game)
    state_graph_filepath = os.path.join(game_enumerated_state_graph_dir, "%s.gpickle" % level)
    if not os.path.exists(state_graph_filepath):
        error_exit("Error: Enumerated state graph for (%s: level %s) does not exist" % (game, level))
    state_graph = nx.read_gpickle(state_graph_filepath)
    return state_graph


def get_coord_metatile_dict(game, level, player_img):
    game_coord_metatile_dicts_dir = "level_saved_files_%s/coord_metatile_dicts/%s/" % (player_img, game)
    coord_metatile_dict_filepath = os.path.join(game_coord_metatile_dicts_dir, "%s.pickle" % level)
    return read_pickle(coord_metatile_dict_filepath)


def get_metatile_num_states_dir(player_img):
    metatile_num_states_dir = "level_saved_files_%s/metatile_num_states/" % player_img
    if not os.path.exists(metatile_num_states_dir):
        os.makedirs(metatile_num_states_dir)
    return metatile_num_states_dir


def main(games, levels, player_img, merge, outfile):

    if len(games) != len(levels):
        error_exit("Given number of games must equal the given number of levels")
    elif len(levels) == 0:
        error_exit("No levels specified")

    metatile_num_states_dir = get_metatile_num_states_dir(player_img)
    metatile_num_states_dict = {}
    unique_metatiles = []
    metatile_str_metatile_dict = {}

    for game, level in zip(games, levels):

        metatile_num_states_dict = {} if not merge else metatile_num_states_dict.copy()  # reset if not merging levels

        state_graph = get_state_graph(game, level, player_img)
        coord_metatile_dict = get_coord_metatile_dict(game, level, player_img)

        for node in state_graph.nodes():
            state_dict = eval(node)
            node_coord = (state_dict['x'], state_dict['y'])
            node_metatile_str = coord_metatile_dict[node_coord]

            # Get standardized string of node metatile
            node_metatile = Metatile.from_str(node_metatile_str)
            if node_metatile not in unique_metatiles:  # have not seen this metatile yet
                unique_metatiles.append(node_metatile)
                metatile_str_metatile_dict[node_metatile_str] = node_metatile

            for metatile_str, metatile in metatile_str_metatile_dict.items():
                if node_metatile == metatile:  # get standardized str of node metatile
                    node_metatile_str = metatile_str
                    break

            # Increment metatile state count
            if metatile_num_states_dict.get(node_metatile_str) is None:
                metatile_num_states_dict[node_metatile_str] = 1
            else:
                metatile_num_states_dict[node_metatile_str] += 1

        if not merge:  # save individual mapping if not merge levels
            outfile_path = os.path.join(metatile_num_states_dir, "%s.json" % level)
            write_json(outfile_path, metatile_num_states_dict)

    if merge:  # save combined mapping if merge levels
        outfile = '_'.join(levels) if outfile is None else outfile
        outfile_path = os.path.join(metatile_num_states_dir, "%s.json" % outfile)
        write_json(outfile_path, metatile_num_states_dict)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get number of states per metatile')
    parser.add_argument('--games', type=str, help='Name of the games')
    parser.add_argument('--levels', type=str, help='Name of the levels')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--merge', type=bool, help='Merge level metatile results', default=True)
    parser.add_argument('--outfile', type=str, help='Outfile name if merging level metatiles', default=None)
    args = parser.parse_args()

    main(args.games, args.levels, args.player_img, args.merge, args.outfile)

