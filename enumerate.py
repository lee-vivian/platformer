'''
Enumerate the state space of a level and extract level metatiles
'''

import pygame
import os
import networkx as nx

import player
import level
from player import Player
from action import Action
from metatile import Metatile

'''
Setup
'''

LEVEL = 1
ENUMERATE_STATES = False  # if False, load in from saved file
EXTRACT_METATILES = False  # if False, load in from saved file
PRINT_METATILE_STATS = True

level = level.Level(LEVEL)

# Background
TILE = 40
FPS = 40  # frame rate
ANI = 4  # animation cycles
clock = pygame.time.Clock()
pygame.init()
world = pygame.display.set_mode([level.world_x, level.world_y])
backdrop = pygame.image.load(os.path.join('images', 'platform_bkgd.png')).convert()
backdropbox = world.get_rect()

# Player
player = player.Player()
player.reset()
player_list = pygame.sprite.Group()
player_list.add(player)

# Level
platform_list = level.platform(TILE)
goal_list = level.goal()


def enumerate_states(start_state, graph, action_set, platform_list, goal_list):

    start_state_str = start_state.to_str()
    graph.add_node(start_state_str)

    unexplored_states = [start_state_str]
    explored_states = []

    while len(unexplored_states) > 0:

        cur_state_str = unexplored_states.pop(0)
        explored_states.append(cur_state_str)

        for action in action_set:
            cur_state = Player.str_to_state(cur_state_str)
            next_state = Player.next_state(cur_state, action, platform_list, goal_list)
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
Enumerate
'''

print("---------------------------------------------------")
print("Enumerating states for Level " + str(LEVEL) + "...")

gpickle_filename = "graph_" + str(LEVEL) + ".gpickle"

if ENUMERATE_STATES:
    action_set = []
    for left in [True, False]:
        for right in [True, False]:
            for jump in [True, False]:
                action_set.append(Action(left, right, jump))
    start_state = Player.start_state()
    graph = nx.DiGraph()
    G = enumerate_states(start_state, graph, action_set, platform_list, goal_list)

    print("--- State Graph for Level " + str(LEVEL) + "---")
    print("Nodes: ", G.number_of_nodes())
    print("Edges: ", G.number_of_edges())

    # SAVE GRAPH
    nx.write_gpickle(G, gpickle_filename)
    print("Saved to: ", gpickle_filename)

else:
    print("Read from: ", gpickle_filename)
    G = nx.read_gpickle(gpickle_filename)

print("Finished enumerating states for level " + str(LEVEL))

# GET METATILE STATS FROM LEVEL

print("---------------------------------------------------")
print("Extracting metatiles for Level " + str(LEVEL) + "...")

metatile_filename = "metatiles_" + str(LEVEL) + ".txt"

if EXTRACT_METATILES:
    level_metatiles = Metatile.extract_metatiles(level, G)

    with open(metatile_filename, 'w') as f:
        for metatile in level_metatiles:
            f.write("%s\n" % metatile.to_str())

    print("level metatiles saved to: " + metatile_filename)

else:
    print("loading level metatiles from: " + metatile_filename)

    f = open(metatile_filename, 'r')
    metatile_strs = f.readlines()
    f.close()

    level_metatiles = []
    for metatile_str in metatile_strs:
        level_metatiles.append(Metatile.from_str(metatile_str))

print("Finished extracting metatiles for level " + str(LEVEL))

if PRINT_METATILE_STATS:

    print("---------------------------------------------------")

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

        if metatile not in unique_metatiles:
            unique_metatiles.append(metatile)
            if graph_not_empty:
                num_unique_metatiles_with_graphs += 1

    print("---- Metatiles for Level " + str(LEVEL) + " ----")
    print("num total metatiles: ",  len(level_metatiles))
    print("num unique metatiles: ", len(unique_metatiles))
    print("num filled metatiles: ", num_filled_metatiles)
    print("num metatiles with graphs: ", num_metatiles_with_graphs)
    print("num unique metatiles with graphs: ", num_unique_metatiles_with_graphs)

