'''
Enumerate the state space of a level
'''

import pygame
import os
import networkx as nx

import player
import level
from player import Player
from action import Action

'''
Setup
'''

LEVEL = 1
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
action_set = []
for left in [True, False]:
    for right in [True, False]:
        for jump in [True, False]:
            action_set.append(Action(left, right, jump))
start_state = Player.start_state()
graph = nx.DiGraph()

print("Start enumerating state tree for LVL", LEVEL, "...")
G = enumerate_states(start_state, graph, action_set, platform_list, goal_list)
print("Finished enumerating state tree for LVL", LEVEL, "...")

print("--- State Graph fo Level " + str(LEVEL) + "---")
print("Nodes: ", G.number_of_nodes())
print("Edges: ", G.number_of_edges())

# SAVE GRAPH
nx.write_gpickle(G, "graph_" + str(LEVEL) + ".gpickle")
print("Saved to: ", "graph_" + str(LEVEL) + ".gpickle")
