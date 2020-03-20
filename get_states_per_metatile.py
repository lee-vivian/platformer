'''
Returns a map of the states associated with each metatile for a given level {metatile_str : {state_coord: 1}}
'''

import argparse
import networkx as nx
import os

from model.metatile import Metatile
import utils


def get_metatile_num_states_dir(player_img):
    directory = "level_saved_files_%s/metatile_num_states/" % player_img
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def get_unique_metatile_strs(game, level, player_img):
    filepath = "level_saved_files_%s/metatile_coords_dicts/%s/%s.pickle" % (player_img, game, level)
    metatile_coords_dict = utils.read_pickle(filepath)
    return list(metatile_coords_dict.keys())


def get_metatile_num_states_dict_from_strs(metatile_strs):
    metatile_num_states_dict = {}
    for m in metatile_strs:
        metatile = Metatile.from_str(m)
        metatile_graph = nx.DiGraph(metatile.graph_as_dict)
        num_states = len(metatile_graph.nodes())
        metatile_num_states_dict[m] = num_states
    return metatile_num_states_dict


def get_metatile_num_states_dict_from_metatiles(metatiles):
    metatile_num_states_dict = {}
    for m in metatiles:
        metatile_str = Metatile.to_str(m)
        metatile_graph = nx.DiGraph(m.graph_as_dict)
        num_states = len(metatile_graph.nodes())
        metatile_num_states_dict[metatile_str] = num_states
    return metatile_num_states_dict


def print_level_stats(level):
    metatile_num_states_file = "level_saved_files_block/metatile_num_states/%s.json" % level
    metatile_num_states_dict = utils.read_json(metatile_num_states_file)
    metatile_count = 0
    total_states = 0
    max_states_per_metatile = 0
    for metatile, num_states in metatile_num_states_dict.items():
        metatile_count += 1
        total_states += num_states
        max_states_per_metatile = max(max_states_per_metatile, num_states)
    print("Level: %s" % level)
    print("Total states: %d" % total_states)
    print("Max states per metatile: %d" % max_states_per_metatile)
    print("Avg states per metatile: %d" % int(total_states / metatile_count))
    exit(0)


def main(games, levels, player_img, merge, outfile):

    if len(games) != len(levels):
            utils.error_exit("Given number of games must equal the given number of levels")
    elif len(levels) == 0:
        utils.error_exit("No levels specified")

    metatile_num_states_dir = get_metatile_num_states_dir(player_img)

    if not merge:
        for game, level in zip(games, levels):
            print("Counting states per metatile for level %s" % level)
            unique_metatile_strs = get_unique_metatile_strs(game, level, player_img)
            metatile_num_states_dict = get_metatile_num_states_dict_from_strs(unique_metatile_strs)
            outfile_path = os.path.join(metatile_num_states_dir, "%s.json" % level)
            utils.write_json(outfile_path, metatile_num_states_dict)
    else:
        print("Counting states per metatile for levels: %s" % str(levels))
        all_metatiles = []
        for game, level in zip(games, levels):
            level_unique_metatile_strs = get_unique_metatile_strs(game, level, player_img)
            all_metatiles += [Metatile.from_str(s) for s in level_unique_metatile_strs]
        unique_metatiles = Metatile.get_unique_metatiles(all_metatiles)
        metatile_num_states_dict = get_metatile_num_states_dict_from_metatiles(unique_metatiles)
        outfile_name = '_'.join(levels) if outfile is None else outfile
        outfile_path = os.path.join(metatile_num_states_dir, "%s.json" % outfile_name)
        utils.write_json(outfile_path, metatile_num_states_dict)


if __name__ == "__main__":
    # games = ['sample', 'sample', 'sample', 'super_mario_bros', 'super_mario_bros', 'kid_icarus']
    # levels = ['sample_mini', 'sample_hallway', 'sample_hallway_flat', 'mario-1-1', 'mario-2-1', 'kidicarus_1']
    #
    # main(games, levels, 'block', merge=False, outfile=None)  # individual levels
    # main(games, levels, 'block', merge=True, outfile='all_levels')  # merge levels

    parser = argparse.ArgumentParser(description='Get number of states per metatile')
    parser.add_argument('--games', type=str, nargs="+", help='Name of the games')
    parser.add_argument('--levels', type=str, nargs="+", help='Name of the levels')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--merge', type=bool, help='Merge level metatile results', default=False)
    parser.add_argument('--outfile', type=str, help='Outfile name if merging level metatiles', default=None)
    args = parser.parse_args()

    main(args.games, args.levels, args.player_img, args.merge, args.outfile)
