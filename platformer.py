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

LEVEL = 1

# Use precomputed graph
USE_GRAPH = True
file_path = "graph_" + str(LEVEL) + ".gpickle"
precomputed_graph = None if not USE_GRAPH else nx.read_gpickle(file_path)
edge_actions_dict = None if not USE_GRAPH else nx.get_edge_attributes(precomputed_graph, "action")

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

'''
Main Loop
'''

main = True

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
    player.update(Action(key_left, key_right, key_jump), platform_list, goal_list, precomputed_graph, edge_actions_dict)
    key_jump = False

    player_list.draw(world)  # draw player
    platform_list.draw(world)  # draw platforms tiles
    goal_list.draw(world)  # draw goal tiles
    pygame.display.flip()
    clock.tick(FPS)
