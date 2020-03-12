'''
Enumerate the state space of a level and extract level metatiles
'''

# Note: use pypy3 to run; use pip_pypy3 to install third-party packages (e.g. networkx)

import os
import networkx as nx
import datetime
import argparse

from model.level import Level
from model.metatile import Metatile
import utils


def get_saved_file_paths(game_name, level_name, player_img):

    level_saved_files_dir = "level_saved_files_%s/" % player_img

    enumerated_state_graphs_dir = level_saved_files_dir + "enumerated_state_graphs/"
    metatiles_dir = level_saved_files_dir + "metatiles/"
    metatile_coords_dict_dir = level_saved_files_dir + "metatile_coords_dicts/"
    coord_metatile_dict_dir = level_saved_files_dir + "coord_metatile_dicts/"

    game_enumerated_state_graphs_dir = enumerated_state_graphs_dir + game_name + "/"
    game_metatiles_dir = metatiles_dir + game_name + "/"
    game_metatile_coords_dict_dir = metatile_coords_dict_dir + game_name + "/"
    game_coord_metatile_dict_dir = coord_metatile_dict_dir + game_name + "/"

    saved_files_directories = [metatiles_dir, metatile_coords_dict_dir, coord_metatile_dict_dir,
                               game_metatiles_dir, game_metatile_coords_dict_dir, game_coord_metatile_dict_dir]

    for directory in saved_files_directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

    state_graph_file = game_enumerated_state_graphs_dir + level_name + ".gpickle"
    metatiles_file = game_metatiles_dir + level_name + ".pickle"
    metatile_coords_dict_file = game_metatile_coords_dict_dir + level_name + ".pickle"
    coord_metatile_dict_file = game_coord_metatile_dict_dir + level_name + ".pickle"

    return state_graph_file, metatiles_file, metatile_coords_dict_file, coord_metatile_dict_file


def get_metatiles(level, state_graph, metatiles_file, metatile_coords_dict_file, coord_metatile_dict_file):
    level_metatiles = Metatile.extract_metatiles(level, state_graph, metatile_coords_dict_file, coord_metatile_dict_file)
    utils.write_pickle(metatiles_file, level_metatiles)
    return level_metatiles


def get_unique_metatile_strs(metatile_coords_dict_file):
    metatile_coords_dict = utils.read_pickle(metatile_coords_dict_file)
    return list(metatile_coords_dict.keys())


def get_metatile_stats_dict(level_metatiles, metatile_coords_dict_file):

    stats_dict = {"num_total_metatiles": 0,
                  "num_filled_metatiles": 0,
                  "num_metatiles_with_graphs": 0,
                  "num_unique_metatiles": 0,
                  "num_unique_metatiles_with_graphs": 0}

    for metatile in level_metatiles:

        stats_dict["num_total_metatiles"] += 1

        if metatile.filled:
            stats_dict["num_filled_metatiles"] += 1

        if bool(metatile.graph_as_dict):  # graph not empty
            stats_dict["num_metatiles_with_graphs"] += 1

    unique_metatile_strs = get_unique_metatile_strs(metatile_coords_dict_file)

    for metatile_str in unique_metatile_strs:

        stats_dict["num_unique_metatiles"] += 1

        metatile = Metatile.from_str(metatile_str)
        if bool(metatile.graph_as_dict):  # graph not empty
            stats_dict["num_unique_metatiles_with_graphs"] += 1

    return stats_dict


def main(game_name, level_name, player_img, print_stats):

    # Create Level
    level = Level.generate_level_from_file("%s/%s.txt" % (game_name, level_name))

    # Level saved file paths
    state_graph_file, metatiles_file, metatile_coords_dict_file, coord_metatile_dict_file = get_saved_file_paths(game_name, level_name, player_img)

    # Retrieve level state graph
    state_graph = nx.read_gpickle(state_graph_file)

    # Extract metatiles
    print("Extracting metatiles for level: " + str(level_name) + " ...")
    start_time = datetime.datetime.now()
    level_metatiles = get_metatiles(level, state_graph, metatiles_file, metatile_coords_dict_file, coord_metatile_dict_file)
    end_time = datetime.datetime.now()
    print("Runtime:", str(end_time-start_time))

    # Calculate Level Metatile Stats
    print("Calculating metatile stats for level: " + str(level_name) + " ...")
    start_time = datetime.datetime.now()
    metatile_stats_dict = get_metatile_stats_dict(level_metatiles, metatile_coords_dict_file)
    end_time = datetime.datetime.now()
    print("Runtime: ", end_time - start_time, "\n")

    metatile_stats_dict["game_name"] = game_name
    metatile_stats_dict["level_name"] = level_name
    metatile_stats_dict['level_width'] = level.width
    metatile_stats_dict['level_height'] = level.height
    metatile_stats_dict['goal_coords'] = str(level.goal_coords)
    metatile_stats_dict['start_coord'] = str(level.start_coord)

    # Save Metatile Stats for Level
    all_levels_info_file = "level_saved_files_%s/all_levels_info.json" % player_img

    if not os.path.exists(all_levels_info_file):
        all_levels_info_contents = {"contents": []}
        utils.write_json(all_levels_info_file, all_levels_info_contents)

    all_levels_info = utils.read_json(all_levels_info_file)

    # Remove duplicate entries per level
    prev_contents = all_levels_info["contents"]
    new_contents = []
    for x in prev_contents:
        if not (x["game_name"] == game_name and x["level_name"] == level_name):
            new_contents.append(x)

    new_contents.append(metatile_stats_dict)
    all_levels_info["contents"] = new_contents

    utils.write_json(all_levels_info_file, all_levels_info)

    if print_stats:
        print("---- Metatiles for Level " + str(level_name) + " ----")
        for key in metatile_stats_dict.keys():
            print(key, ": ", metatile_stats_dict.get(key))


if __name__ == "__main__":

    # GAME_LEVEL_PAIRS = [
    #     ('sample', 'sample_mini'),
    #     ('sample', 'sample_hallway'),
    #     ('sample', 'sample_hallway_flat'),
    #     ('super_mario_bros', 'mario-1-1'),
    #     ('super_mario_bros', 'mario-2-1'),
    #     ('kid_icarus', 'kidicarus_1')
    # ]
    #
    # for game, level in GAME_LEVEL_PAIRS:
    #     main(game, level, 'block', True)

    parser = argparse.ArgumentParser(description='Extract metatiles for the given level')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--print_stats', type=bool, help='Print metatile stats for the level', default=True)
    args = parser.parse_args()

    main(args.game, args.level, args.player_img, args.print_stats)


