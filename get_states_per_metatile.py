'''
Returns a map of the states associated with each metatile for a given level {metatile_str : {state_coord: 1}}
'''

import argparse
import networkx as nx
import os
import datetime

from model.metatile import Metatile
from model.player import Player
import utils


def print_stats():
    import json
    saved_files = ['sample_mini', 'sample_hallway', 'sample_hallway_flat', 'mario-1-1', 'mario-2-1', 'kidicarus_1', 'all_levels']
    for sf in saved_files:
        filepath = "level_saved_files_block/metatile_states_dicts/%s.json" % sf
        with open(filepath, 'r') as file:
            contents = json.load(file)
        file.close()

        total_num_states = 0
        max_states_per_metatile = 0
        for metatile, states_dict in contents.items():
            total_num_states += len(states_dict)
            max_states_per_metatile = max(max_states_per_metatile, len(states_dict))

        print("\nLevel:", sf)
        print("Total number of states: %d" % total_num_states)
        print("Max states per metatile: %d" % max_states_per_metatile)


def get_state_graph(game, level, player_img):
    game_enumerated_state_graph_dir = "level_saved_files_%s/enumerated_state_graphs/%s/" % (player_img, game)
    state_graph_filepath = os.path.join(game_enumerated_state_graph_dir, "%s.gpickle" % level)
    if not os.path.exists(state_graph_filepath):
        utils.error_exit("Error: Enumerated state graph for (%s: level %s) does not exist" % (game, level))
    state_graph = nx.read_gpickle(state_graph_filepath)
    return state_graph


def get_coord_metatile_dict(game, level, player_img):
    game_coord_metatile_dicts_dir = "level_saved_files_%s/coord_metatile_dicts/%s/" % (player_img, game)
    coord_metatile_dict_filepath = os.path.join(game_coord_metatile_dicts_dir, "%s.pickle" % level)
    return utils.read_pickle(coord_metatile_dict_filepath)


def get_metatile_states_dicts_dir(player_img):
    metatile_states_dicts_dir = "level_saved_files_%s/metatile_states_dicts/" % player_img
    if not os.path.exists(metatile_states_dicts_dir):
        os.makedirs(metatile_states_dicts_dir)
    return metatile_states_dicts_dir


def main(games, levels, player_img, merge, outfile):

    if len(games) != len(levels):
        utils.error_exit("Given number of games must equal the given number of levels")
    elif len(levels) == 0:
        utils.error_exit("No levels specified")

    metatile_states_dicts_dir = get_metatile_states_dicts_dir(player_img)
    metatile_states_dict = {}
    unique_metatiles = []
    metatile_str_metatile_dict = {}

    for game, level in zip(games, levels):

        print("Calculating states per metatile for level %s ..." % level)
        start_time = datetime.datetime.now()

        if not merge:  # reset if not merging levels
            metatile_states_dict = {}
            unique_metatiles = []
            metatile_str_metatile_dict = {}

        state_graph = get_state_graph(game, level, player_img)
        coord_metatile_dict = get_coord_metatile_dict(game, level, player_img)

        for node in state_graph.nodes():
            state_dict = eval(node)
            state_coord = (state_dict['x'], state_dict['y'])
            node_metatile_coord = (Player.metatile_coord_from_state_coord(state_coord, player_img))
            node_metatile_str = coord_metatile_dict[node_metatile_coord]

            # Get standardized string of node metatile
            node_metatile = Metatile.from_str(node_metatile_str)
            if node_metatile not in unique_metatiles:  # have not seen this metatile yet
                unique_metatiles.append(node_metatile)
                metatile_str_metatile_dict[node_metatile_str] = node_metatile

            for metatile_str, metatile in metatile_str_metatile_dict.items():
                if node_metatile == metatile:  # get standardized str of node metatile
                    node_metatile_str = metatile_str
                    break

            state_coord_str = str(state_coord)

            # Increment metatile state count
            if metatile_states_dict.get(node_metatile_str) is None:  # metatile_str not seen yet
                metatile_states_dict[node_metatile_str] = {state_coord_str: 1}
            else:
                if metatile_states_dict.get(node_metatile_str).get(state_coord_str) is None:
                    metatile_states_dict[node_metatile_str][state_coord_str] = 1  # state not seen at cur metatile yet

        end_time = datetime.datetime.now()
        print("Runtime: %s" % str(end_time-start_time))

        if not merge:  # save individual mapping if not merge levels
            outfile_path = os.path.join(metatile_states_dicts_dir, "%s.json" % level)
            utils.write_json(outfile_path, metatile_states_dict)

    if merge:  # save combined mapping if merge levels
        outfile = '_'.join(levels) if outfile is None else outfile
        outfile_path = os.path.join(metatile_states_dicts_dir, "%s.json" % outfile)
        utils.write_json(outfile_path, metatile_states_dict)


if __name__ == "__main__":

    games = ['sample', 'sample', 'sample', 'super_mario_bros', 'super_mario_bros', 'kid_icarus']
    levels = ['sample_mini', 'sample_hallway', 'sample_hallway_flat', 'mario-1-1', 'mario-2-1', 'kidicarus_1']
    main(games, levels, 'block', merge=False, outfile=None)

    main(games, levels, 'block', merge=True, outfile='all_levels')

    # parser = argparse.ArgumentParser(description='Get number of states per metatile')
    # parser.add_argument('--games', type=str, nargs="+", help='Name of the games')
    # parser.add_argument('--levels', type=str, nargs="+", help='Name of the levels')
    # parser.add_argument('--player_img', type=str, help='Player image', default='block')
    # parser.add_argument('--merge', type=bool, help='Merge level metatile results', default=False)
    # parser.add_argument('--outfile', type=str, help='Outfile name if merging level metatiles', default=None)
    # args = parser.parse_args()
    #
    # main(args.games, args.levels, args.player_img, args.merge, args.outfile)

