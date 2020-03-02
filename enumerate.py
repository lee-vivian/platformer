'''
Enumerate the state space of a level and extract level metatiles
'''

# Note: use pypy3 to run; use pip_pypy3 to install third-party packages (e.g. networkx)

import os
import networkx as nx
import datetime

from model.player import Player as PlayerModel
from model.level import Level
from model.action import Action
from model.metatile import Metatile


def get_saved_file_paths(level_name, player_img):

    level_saved_files_dir = "level_saved_files_" + player_img + "/"
    enumerated_state_graphs_dir = level_saved_files_dir + "enumerated_state_graphs/"
    metatiles_dir = level_saved_files_dir + "metatiles/"
    coord_metatile_dicts_dir = level_saved_files_dir + "coord_metatile_dicts/"
    metatile_coords_dict_dir = level_saved_files_dir + "metatile_coords_dicts/"

    if not os.path.exists(level_saved_files_dir):
        os.makedirs(level_saved_files_dir)
        os.makedirs(enumerated_state_graphs_dir)
        os.makedirs(metatiles_dir)
        os.makedirs(coord_metatile_dicts_dir)
        os.makedirs(metatile_coords_dict_dir)

    state_graph_file = enumerated_state_graphs_dir + str(level_name) + ".gpickle"
    metatiles_file = metatiles_dir + str(level_name) + ".txt"
    coord_metatile_dict_file = coord_metatile_dicts_dir + str(level_name) + ".txt"
    metatile_coords_dict_file = metatile_coords_dict_dir + str(level_name) + ".txt"

    return state_graph_file, metatiles_file, coord_metatile_dict_file, metatile_coords_dict_file


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


def get_metatiles(level, state_graph, metatiles_file, coord_metatile_dict_file, recompute_metatiles):
    if recompute_metatiles:

        level_metatiles, coord_to_metatile_str_dict = Metatile.extract_metatiles(level, state_graph)

        with open(metatiles_file, 'w') as f:
            for metatile in level_metatiles:
                f.write("%s\n" % metatile.to_str())
        f.close()
        print("Saved to: ", metatiles_file)

        with open(coord_metatile_dict_file, 'w') as f:
            f.write(str(coord_to_metatile_str_dict))
        f.close()
        print("Saved to: ", coord_metatile_dict_file)

    else:

        f = open(metatiles_file, 'r')
        metatile_strs = f.readlines()
        f.close()

        level_metatiles = []
        for metatile_str in metatile_strs:
            level_metatiles.append(Metatile.from_str(metatile_str))

        f = open(coord_metatile_dict_file, 'r')
        coord_to_metatile_str_dict = eval(f.readline())
        f.close()

    return level_metatiles, coord_to_metatile_str_dict


def get_metatile_stats_dict(level_metatiles):
    stats_dict = {"num_filled_metatiles": 0,
                  "num_metatiles_with_graphs": 0,
                  "unique_metatiles": [],
                  "num_unique_metatiles_with_graphs": 0}

    for metatile in level_metatiles:

        graph_not_empty = bool(metatile.graph_as_dict)

        if metatile.filled:
            stats_dict["num_filled_metatiles"] += 1

        if graph_not_empty:
            stats_dict["num_metatiles_with_graphs"] += 1

        if metatile not in stats_dict.get("unique_metatiles"):  # if metatile has not been seen yet
            stats_dict["unique_metatiles"].append(metatile)
            if graph_not_empty:
                stats_dict["num_unique_metatiles_with_graphs"] += 1

    return stats_dict


def construct_metatile_coords_dict(unique_metatiles, coord_to_metatile_str_dict, metatile_coords_dict_file):
    metatile_to_coords_dict = {}

    for metatile in unique_metatiles:
        metatile_to_coords_dict[metatile.to_str()] = []
        coords_to_check = list(coord_to_metatile_str_dict.keys())

        for coord in coords_to_check:
            metatile_at_coord = Metatile.from_str(coord_to_metatile_str_dict[coord])
            if metatile_at_coord == metatile:
                metatile_to_coords_dict[metatile.to_str()].append(coord)
                del coord_to_metatile_str_dict[coord]  # remove coord from dict to speed up future checks

    with open(metatile_coords_dict_file, 'w') as f:
        f.write(str(metatile_to_coords_dict))
    f.close()
    print("Saved to: ", metatile_coords_dict_file)


def main(game_name, level_name, player_img):

    main_start_time = datetime.datetime.now()

    # Create Level
    level = Level.generate_level_from_file(game_name + "/" + level_name + ".txt")

    # Level saved file paths
    state_graph_file, metatiles_file, coord_metatile_dict_file, metatile_coords_dict_file = get_saved_file_paths(player_img, level_name)

    # Enumerate State Graph
    print("Enumerating states for level: " + str(level_name) + "...")
    start_time = datetime.datetime.now()
    state_graph = get_state_graph(level, state_graph_file, ENUMERATE_STATES, player_img)
    end_time = datetime.datetime.now()
    print("Runtime: ", end_time - start_time)

    # Extract Metatiles
    print("Extracting metatiles for level: " + str(level_name) + "...")
    start_time = datetime.datetime.now()
    level_metatiles, coord_to_metatile_str_dict = get_metatiles(level, state_graph, metatiles_file,
                                                                coord_metatile_dict_file, EXTRACT_METATILES)
    end_time = datetime.datetime.now()
    print("Runtime: ", end_time - start_time)

    print("Calculating metatile stats for level: " + str(level_name))
    start_time = datetime.datetime.now()
    metatile_stats_dict = get_metatile_stats_dict(level_metatiles)
    end_time = datetime.datetime.now()
    print("Runtime: ", end_time - start_time)

    # Compute {Metatile: Coords} Dict (used to view metatiles on level foreground)
    if COMPUTE_METATILE_COORDS_DICT:
        start_time = datetime.datetime.now()
        print("Constructing {metatile: coords} dict for level: " + str(level))
        construct_metatile_coords_dict(metatile_stats_dict.get("unique_metatiles"), coord_to_metatile_str_dict,
                                       metatile_coords_dict_file)
        end_time = datetime.datetime.now()
        print("Runtime: ", end_time - start_time)

    # Print Metatile Stats
    print("---- Metatiles for Level " + str(level_name) + " ----")
    print("num total metatiles: ", len(level_metatiles))
    print("num filled metatiles: ", metatile_stats_dict.get("num_filled_metatiles"))
    print("num unique metatiles: ", len(metatile_stats_dict.get("unique_metatiles")))
    print("num unique metatiles with graphs: ", metatile_stats_dict.get("num_unique_metatiles_with_graphs"))
    print("num metatiles with graphs: ", metatile_stats_dict.get("num_metatiles_with_graphs"))

    main_end_time = datetime.datetime.now()
    print("\n Total Program Runtime: ", main_end_time - main_start_time)


if __name__ == "__main__":

    GAME = "sample"
    LEVEL = "sample_hallway"
    PLAYER_IMG = "block"

    ENUMERATE_STATES = True  # if False, load in from saved file
    EXTRACT_METATILES = True  # if False, load in from saved file
    COMPUTE_METATILE_COORDS_DICT = True  # if False, load in from saved file
    PRINT_METATILE_STATS = True

    main(GAME, LEVEL, PLAYER_IMG)



