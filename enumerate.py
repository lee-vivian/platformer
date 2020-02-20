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
from state import State
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


def str_to_state(string):
    state_dict = eval(string)
    return State(state_dict['x'], state_dict['y'],
                 state_dict['movex'], state_dict['movey'],
                 state_dict['facing_right'], state_dict['onground'], state_dict['goal_reached'])


# @TODO update method to create graph of state strings instead of States
def enumerate_states(start_state, graph, action_set, platform_list, goal_list):

    start_state_str = start_state.to_str()
    graph.add_node(start_state_str)
    unexplored_states = [start_state_str]
    explored_states = []

    while len(unexplored_states) > 0:

        cur_state_str = unexplored_states.pop(0)
        explored_states.append(cur_state_str)

        for action in action_set:

            cur_state = str_to_state(cur_state_str)
            next_state = Player.next_state(cur_state, action, platform_list, goal_list)
            next_state_str = next_state.to_str()
            if next_state_str not in explored_states and next_state_str not in unexplored_states:
                graph.add_node(next_state_str)
                unexplored_states.append(next_state_str)
            graph.add_edge(cur_state_str, next_state_str, action=action)

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

