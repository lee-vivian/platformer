'''
Enumerate the state space of a level and extract level metatiles
'''

# Note: use pypy3 to run; use pip_pypy3 to install third-party packages (e.g. networkx)

import os
import networkx as nx
import datetime
import json

from model.player import Player as PlayerModel
from model.level import Level
from model.action import Action
from model.metatile import Metatile


def get_saved_file_paths(game_name, level_name, player_img):

    level_saved_files_dir = "level_saved_files_" + player_img + "/"

    enumerated_state_graphs_dir = level_saved_files_dir + "enumerated_state_graphs/"
    metatiles_dir = level_saved_files_dir + "metatiles/"
    metatile_coords_dict_dir = level_saved_files_dir + "metatile_coords_dicts/"
    coord_metatile_dict_dir = level_saved_files_dir + "coord_metatile_dicts/"

    game_enumerated_state_graphs_dir = enumerated_state_graphs_dir + game_name + "/"
    game_metatiles_dir = metatiles_dir + game_name + "/"
    game_metatile_coords_dict_dir = metatile_coords_dict_dir + game_name + "/"
    game_coord_metatile_dict_dir = coord_metatile_dict_dir + game_name + "/"

    saved_files_directories = [level_saved_files_dir,
                               enumerated_state_graphs_dir, metatiles_dir, metatile_coords_dict_dir, coord_metatile_dict_dir,
                               game_enumerated_state_graphs_dir, game_metatiles_dir, game_metatile_coords_dict_dir, game_coord_metatile_dict_dir]

    for directory in saved_files_directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

    state_graph_file = game_enumerated_state_graphs_dir + str(level_name) + ".gpickle"
    metatiles_file = game_metatiles_dir + str(level_name) + ".txt"
    metatile_coords_dict_file = game_metatile_coords_dict_dir + str(level_name) + ".txt"
    coord_metatile_dict_file = game_coord_metatile_dict_dir + str(level_name) + ".txt"

    return state_graph_file, metatiles_file, metatile_coords_dict_file, coord_metatile_dict_file


def get_action_set():
    action_set = []
    for left in [True, False]:
        for right in [True, False]:
            for jump in [True, False]:
                action_set.append(Action(left, right, jump))
    return action_set


def enumerate_states(player_model, start_state, graph, action_set, platform_coords, goal_coords):
    start_state_str = start_state.to_str()
    graph.add_node(start_state_str)

    unexplored_states = [start_state_str]
    explored_states = []

    while len(unexplored_states) > 0:

        cur_state_str = unexplored_states.pop(0)
        explored_states.append(cur_state_str)

        for action in action_set:
            cur_state = PlayerModel.str_to_state(cur_state_str)
            next_state = player_model.next_state(cur_state, action, platform_coords, goal_coords)
            next_state_str = next_state.to_str()
            if next_state_str not in explored_states and next_state_str not in unexplored_states:
                graph.add_node(next_state_str)
                unexplored_states.append(next_state_str)
            if not graph.has_edge(cur_state_str, next_state_str):
                graph.add_edge(cur_state_str, next_state_str, action=[action.to_str()])
            else:
                graph.get_edge_data(cur_state_str, next_state_str)["action"].append(action.to_str())

    return graph


def get_state_graph(level, state_graph_file, player_img, recompute_graph):
    if recompute_graph:
        player_model = PlayerModel(player_img)
        start_state = player_model.start_state()
        action_set = get_action_set()
        state_graph = enumerate_states(player_model, start_state, nx.DiGraph(), action_set, level.platform_coords,
                                       level.goal_coords)
        nx.write_gpickle(state_graph, state_graph_file)
        print("Saved to: ", state_graph_file)

    else:
        print("Read from: ", state_graph_file)
        state_graph = nx.read_gpickle(state_graph_file)

    return state_graph


def get_metatiles(level, state_graph, metatiles_file, metatile_coords_dict_file, coord_metatile_dict_file, recompute_metatiles):

    if recompute_metatiles:
        level_metatiles = Metatile.extract_metatiles(level, state_graph, metatile_coords_dict_file, coord_metatile_dict_file)
        with open(metatiles_file, 'w') as f:
            for metatile in level_metatiles:
                f.write("%s\n" % metatile.to_str())
        f.close()
        print("Saved to: ", metatiles_file)

    else:
        f = open(metatiles_file, 'r')
        metatile_strs = f.readlines()
        f.close()
        level_metatiles = []
        for metatile_str in metatile_strs:
            level_metatiles.append(Metatile.from_str(metatile_str))

    return level_metatiles


def get_unique_metatile_strs(metatile_coords_dict_file):
    f = open(metatile_coords_dict_file, 'r')
    metatile_coords_dict = eval(f.readline())
    f.close()
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


def main(game_name, level_name, player_img):

    main_start_time = datetime.datetime.now()

    # Create Level
    level = Level.generate_level_from_file(game_name + "/" + level_name + ".txt")

    # Level saved file paths
    state_graph_file, metatiles_file, metatile_coords_dict_file, coord_metatile_dict_file = get_saved_file_paths(game_name, level_name, player_img)

    # Enumerate State Graph
    print("\nEnumerating states for level: " + str(level_name) + " ...")
    start_time = datetime.datetime.now()
    state_graph = get_state_graph(level, state_graph_file, player_img, ENUMERATE_STATES)
    end_time = datetime.datetime.now()
    print("Runtime: ", end_time - start_time, "\n")

    # Extract Metatiles
    print("Extracting metatiles for level: " + str(level_name) + " ...")
    start_time = datetime.datetime.now()
    level_metatiles = get_metatiles(level, state_graph, metatiles_file, metatile_coords_dict_file, coord_metatile_dict_file, EXTRACT_METATILES)
    end_time = datetime.datetime.now()
    print("Runtime: ", end_time - start_time, "\n")

    # Calculate Level Metatile Stats
    print("Calculating metatile stats for level: " + str(level_name) + " ...")
    start_time = datetime.datetime.now()
    metatile_stats_dict = get_metatile_stats_dict(level_metatiles, metatile_coords_dict_file)
    end_time = datetime.datetime.now()
    print("Runtime: ", end_time - start_time, "\n")

    main_end_time = datetime.datetime.now()
    metatile_stats_dict["game_name"] = game_name
    metatile_stats_dict["level_name"] = level_name
    metatile_stats_dict['level_width'] = level.width
    metatile_stats_dict['level_height'] = level.height
    metatile_stats_dict['goal_coords'] = str(level.goal_coords)
    metatile_stats_dict["total_runtime"] = str(main_end_time - main_start_time)

    # Save Metatile Stats for Level
    all_levels_info_file = "level_saved_files_" + player_img + "/all_levels_info.json"

    with open(all_levels_info_file, 'r') as all_levels_file:
        all_levels_info = json.load(all_levels_file)

    # Remove duplicate entries per level
    prev_contents = all_levels_info["contents"]

    new_contents = []
    for x in prev_contents:
        if not (x["game_name"] == game_name and x["level_name"] == level_name):
            new_contents.append(x)

    # Save original runtime (max time req to enumerate state graph and extract metatiles)
    for level_stats in prev_contents:
        if level_stats["level_name"] == level_name:
            metatile_stats_dict["total_runtime"] = level_stats["total_runtime"]

    new_contents.append(metatile_stats_dict)
    all_levels_info["contents"] = new_contents

    with open(all_levels_info_file, "w") as all_levels_file:
        json.dump(all_levels_info, all_levels_file, indent=2, sort_keys=True)

    if PRINT_METATILE_STATS:
        print("---- Metatiles for Level " + str(level_name) + " ----")
        for key in metatile_stats_dict.keys():
            print(key, ": ", metatile_stats_dict.get(key))

    print("\nProgram Runtime: ", main_end_time - main_start_time)


if __name__ == "__main__":

    PLAYER_IMG = "block"

    GAME_AND_LEVEL = [
        ('sample', 'sample_mini'),
        ('sample', 'sample_hallway_flat'),
        ('sample', 'sample_hallway'),
        ('kid_icarus', 'kidicarus_1'),
        ('super_mario_bros', 'mario-1-1'),
        ('super_mario_bros', 'mario-2-1')
    ]

    ENUMERATE_STATES = False  # if False, load in from saved file
    EXTRACT_METATILES = False  # if False, load in from saved file
    PRINT_METATILE_STATS = True

    for game, level in GAME_AND_LEVEL:
        main(game, level, PLAYER_IMG)
