'''
Dump info about the precomputed state graph.
'''

# Note: use pypy3 to run; use pip_pypy3 to install third-party packages (e.g. networkx)

import os
import networkx as nx
import datetime
import argparse

def get_state_graph_file(game_name, level_name, player_img):
    level_saved_files_dir = "level_saved_files_%s/" % player_img
    enumerated_state_graphs_dir = level_saved_files_dir + "enumerated_state_graphs/"
    game_enumerated_state_graphs_dir = enumerated_state_graphs_dir + game_name + "/"
    saved_files_directories = [level_saved_files_dir, enumerated_state_graphs_dir, game_enumerated_state_graphs_dir]

    for directory in saved_files_directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

    state_graph_file = game_enumerated_state_graphs_dir + str(level_name) + ".gpickle"
    return state_graph_file


def main(game_name, level_name, player_img):
    # Level saved file paths
    state_graph_file = get_state_graph_file(game_name, level_name, player_img)

    # Retrieve level state graph
    state_graph = nx.read_gpickle(state_graph_file)

    # print
    for node in state_graph.nodes:
        print(node)

    for node in state_graph.nodes:
        print()
        print(node)
        for edge in state_graph.out_edges(node):
            print(' ' * 10, '->', ','.join(state_graph.edges[edge]["action"]), '->', edge[1])



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract metatiles for the given level')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    args = parser.parse_args()

    main(args.game, args.level, args.player_img)
