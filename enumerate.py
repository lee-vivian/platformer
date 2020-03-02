'''
Enumerate the state space of a level and extract level metatiles
'''

import os
import networkx as nx
import datetime

from model.player import Player as PlayerModel
from model.level import Level
from model.action import Action
from model.metatile import Metatile

# use pypy3 to run; use pip_pypy3 to install third-party packages (e.g. networkx)

'''
Setup
'''

GAME = "sample"
LEVEL = "sample_hallway"

PLAYER_IMG = 'block'

ENUMERATE_STATES = True  # if False, load in from saved file
EXTRACT_METATILES = True  # if False, load in from saved file
COMPUTE_METATILE_COORDS_DICT = True  # if False, load in from saved file
PRINT_METATILE_STATS = True

# Create Level
level = Level.generate_level_from_file(GAME + "/" + LEVEL + ".txt")

# Level saved files

level_saved_files_dir = "level_saved_files_" + PLAYER_IMG + "/"
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

state_graph_file = enumerated_state_graphs_dir + str(LEVEL) + ".gpickle"
metatiles_file = metatiles_dir + str(LEVEL) + ".txt"
coord_metatile_dict_file = coord_metatile_dicts_dir + str(LEVEL) + ".txt"
metatile_coords_dict_file = metatile_coords_dict_dir + str(LEVEL) + ".txt"


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


'''
Enumerate State Graph
'''

time1 = datetime.datetime.now()
print("Start: ", time1)

print("---------------------------------------------------")
print("Enumerating states for level: " + str(LEVEL) + "...")

if ENUMERATE_STATES:

    player_model = PlayerModel(PLAYER_IMG)
    start_state = player_model.start_state()
    graph = nx.DiGraph()
    action_set = []
    for left in [True, False]:
        for right in [True, False]:
            for jump in [True, False]:
                action_set.append(Action(left, right, jump))
    G = enumerate_states(player_model, start_state, graph, action_set, level.platform_coords, level.goal_coords)

    print("--- State Graph for Level " + str(LEVEL) + "---")
    print("Nodes: ", G.number_of_nodes())
    print("Edges: ", G.number_of_edges())

    # SAVE GRAPH
    nx.write_gpickle(G, state_graph_file)
    print("Saved to: ", state_graph_file)

else:
    print("Read from: ", state_graph_file)
    G = nx.read_gpickle(state_graph_file)

print("Finished enumerating states for level: " + str(LEVEL))
time2 = datetime.datetime.now()
print("Runtime: ", time2-time1)

'''
Extract Metatiles
'''

print("---------------------------------------------------")
print("Extracting metatiles for level: " + str(LEVEL) + "...")


if EXTRACT_METATILES:
    level_metatiles, coord_to_metatile_str_dict = Metatile.extract_metatiles(level, G)

    with open(metatiles_file, 'w') as f:
        for metatile in level_metatiles:
            f.write("%s\n" % metatile.to_str())
    f.close()

    print("Level metatiles saved to: " + metatiles_file)

    with open(coord_metatile_dict_file, 'w') as f:
        f.write(str(coord_to_metatile_str_dict))
    f.close()

    print("Level {coord: metatile} dict saved to: " + coord_metatile_dict_file)

else:
    print("Loading level metatiles from: " + metatiles_file)

    f = open(metatiles_file, 'r')
    metatile_strs = f.readlines()
    f.close()

    level_metatiles = []
    for metatile_str in metatile_strs:
        level_metatiles.append(Metatile.from_str(metatile_str))

    print("Loading level {coord: metatile} dict from: " + coord_metatile_dict_file)

    f = open(coord_metatile_dict_file, 'r')
    coord_to_metatile_str_dict = eval(f.readline())
    f.close()

print("Finished extracting metatiles for level: " + str(LEVEL))
time3 = datetime.datetime.now()
print("Runtime: ", time3-time2)

if PRINT_METATILE_STATS:

    print("---------------------------------------------------")
    print("Printing metatile stats for level: " + str(LEVEL))

    num_filled_metatiles = 0
    num_metatiles_with_graphs = 0
    unique_metatiles = []
    num_unique_metatiles_with_graphs = 0

    for metatile in level_metatiles:

        graph_not_empty = bool(metatile.graph_as_dict)

        if metatile.filled:
            num_filled_metatiles += 1

        if graph_not_empty:
            num_metatiles_with_graphs += 1

        if metatile not in unique_metatiles:  # if metatile has not been seen yet

            unique_metatiles.append(metatile)

            if graph_not_empty:
                num_unique_metatiles_with_graphs += 1

    print("Retrieving {metatile: coords} dict for level: " + str(LEVEL))

    if COMPUTE_METATILE_COORDS_DICT:  # {metatile: list-of-tile-coords}

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

        print("Level {metatile: coords} dict saved to: " + metatile_coords_dict_file)

    else:
        print("Loading level metatile_to_coords_dict from: " + metatile_coords_dict_file)
        f = open(metatile_coords_dict_file, 'r')
        metatile_to_coords_dict = eval(f.readline())
        f.close()

    time4 = datetime.datetime.now()
    print("Runtime: ", time4 - time3)

    print("---- Metatiles for Level " + str(LEVEL) + " ----")
    print("num total metatiles: ",  len(level_metatiles))
    print("num filled metatiles: ", num_filled_metatiles)
    print("num unique metatiles: ", len(unique_metatiles))
    print("num unique metatiles with graphs: ", num_unique_metatiles_with_graphs)
    print("num metatiles with graphs: ", num_metatiles_with_graphs)

    print("--- Tile Coords Grouped by Metatile for Level " + str(LEVEL) + " ----")
    for coords_with_same_metatile in metatile_to_coords_dict.values():
        if len(coords_with_same_metatile) > 1:
            print(coords_with_same_metatile)

    time5 = datetime.datetime.now()
    print("\n Total Runtime: ", time5-time1)

