'''
Enumerate the state space of a level
'''

import pygame
import os
import networkx as nx
# import json
# from json import JSONEncoder

import player
import level
from player import Player
from action import Action
from metatile import Metatile

'''
Setup
'''

LEVEL = 1
RERUN_ENUMERATE_STATES = False

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

gpickle_filename = "graph_" + str(LEVEL) + ".gpickle"

if RERUN_ENUMERATE_STATES:
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
    G = nx.read_gpickle(gpickle_filename)

# EXTRACT METATILES FROM LEVEL
level_metatiles = Metatile.extract_tiles(level, G)

total_metatiles = 0
filled_metatiles = 0
metatiles_with_graphs = 0

for tile in level_metatiles:

    total_metatiles += 1

    if tile.filled:
        filled_metatiles += 1

    # if grid cell's graph is not empty
    if bool(tile.graph_as_dict):
        metatiles_with_graphs += 1

print("---- LEVEL " + str(LEVEL) + " ----")
print("total cells: " + str(total_metatiles))
print("filled cells: " + str(filled_metatiles))
print("cells with graphs: " + str(metatiles_with_graphs))


# # @TODO save level metatiles - FIX
# class MetatileEncoder(JSONEncoder):
#
#     def default(self, metatile):
#         return metatile.__dict__
#
#
# with open(graph_level + ".json", "w") as write:
#     json.dumps(level_metatiles, cls=MetatileEncoder)
#
# print("Level Metatiles  saved to: " + graph_level + ".json")


