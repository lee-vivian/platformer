'''
Enumerate the state space of a level
'''

import pygame
import sys
import os
import networkx as nx

import player
from player import Player
import level
from action import Action

'''
Setup
'''

LEVEL = 1

# Background
if LEVEL == 0:
    WORLDX = 240
    WORLDY = 200
else:
    WORLDX = 960
    WORLDY = 720

TILE = 40
FPS = 40  # frame rate
ANI = 4  # animation cycles
clock = pygame.time.Clock()
pygame.init()
world = pygame.display.set_mode([WORLDX, WORLDY])
backdrop = pygame.image.load(os.path.join('images', 'platform_bkgd.png')).convert()
backdropbox = world.get_rect()

# Player
player = player.Player()
player.reset()
player_list = pygame.sprite.Group()
player_list.add(player)
STEPS = 5  # num pixels to move per step

# Level
level = level.Level()
platform_list = level.platform(LEVEL, TILE, WORLDX, WORLDY)
goal_list = level.goal(LEVEL)


def enumerate_states(start_state, graph, action_set, platform_list, goal_list):

    graph.add_node(start_state)
    unexplored_states = [start_state]
    unexplored_states_str = [start_state.to_str()]
    explored_states_str = []

    while len(unexplored_states) > 0:

        cur_state = unexplored_states.pop(0)
        unexplored_states_str.pop(0)
        explored_states_str.append(cur_state.to_str())
        print(cur_state.to_str())

        for action in action_set:
            next_state = Player.next_state(cur_state, action, platform_list, goal_list)
            next_state_str = next_state.to_str()
            if next_state_str not in explored_states_str and next_state_str not in unexplored_states_str:
                graph.add_node(next_state)
                graph.add_edge(cur_state, next_state)
                unexplored_states.append(next_state)
                unexplored_states_str.append(next_state_str)

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
graph = nx.Graph()

orig_stdout = sys.stdout
f = open('enumerated_states.txt', 'w')
sys.stdout = f

print("Start enumerating state tree for LVL", LEVEL, "...")
G = enumerate_states(start_state, graph, action_set, platform_list, goal_list)

sys.stdout = orig_stdout
f.close()

print("Nodes: ", G.number_of_nodes())
print("Edges: ", G.number_of_edges())

