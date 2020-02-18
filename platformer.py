'''
Basic Platform Game
author: Vivian Lee
created: 02-12-2020
acknowledgements: followed tutorial from opensource.com
'''

import pygame
import sys
import os
import networkx as nx

import player
import level
from action import Action

'''
Setup
'''

# Background
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
LEVEL = 1
level = level.Level()
platform_list = level.platform(LEVEL, TILE, WORLDX, WORLDY)
goal_list = level.goal(LEVEL)

'''
Enumerating the State Tree
'''

left_options = [True, False]
right_options = [True, False]
jump_options = [True, False]
action_set = []

for l in left_options:
    for r in right_options:
        for j in jump_options:
            action_set.append(Action(l, r, j))

start_state = player.start_state()
graph = nx.Graph()
graph.add_node(start_state)


def enumerate_states(start_state, graph, action_set, platform_list, goal_list):
    for action in action_set:
        next_state = player.next_state(start_state, action, platform_list, goal_list)
        if not graph.has_node(next_state):
            graph.add_node(next_state)
            graph.add_edge(start_state, next_state)
            enumerate_states(next_state, graph, action_set, platform_list, goal_list)
    return graph


G = enumerate_states(start_state, graph, action_set, platform_list, goal_list)
print("Nodes: ", G.number_of_nodes())
print("Edges: ", G.number_of_edges())



'''
Main Loop
'''

main = False

key_left = False
key_right = False
key_jump = False

while main:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            main = False

        if event.type == pygame.KEYDOWN:
            if event.key == ord('q'):
                pygame.quit()
                main = False
                sys.exit()
            elif event.key == ord('r'):
                player.reset()
            elif event.key in [pygame.K_LEFT, ord('a')]:
                key_left = True
            elif event.key in [pygame.K_RIGHT, ord('d')]:
                key_right = True
            elif event.key in [pygame.K_SPACE, pygame.K_UP, ord('w')]:
                key_jump = True

        if event.type == pygame.KEYUP:
            if event.key in [pygame.K_LEFT, ord('a')]:
                key_left = False
            elif event.key in [pygame.K_RIGHT, ord('d')]:
                key_right = False

    world.blit(backdrop, backdropbox)
    player.update(Action(key_left, key_right, key_jump), platform_list, goal_list)
    key_jump = False

    player_list.draw(world)  # draw player
    platform_list.draw(world)  # draw platforms tiles
    goal_list.draw(world)  # draw goal tiles
    pygame.display.flip()
    clock.tick(FPS)
