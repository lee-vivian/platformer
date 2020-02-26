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
level = level.Level(LEVEL)
DRAW_METATILE_LABELS = False

# Use precomputed graph
USE_GRAPH = True
file_path = "graph_" + str(LEVEL) + ".gpickle"
precomputed_graph = None if not USE_GRAPH else nx.read_gpickle(file_path)
edge_actions_dict = None if not USE_GRAPH else nx.get_edge_attributes(precomputed_graph, "action")

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

if DRAW_METATILE_LABELS:

    FONT_COLOR = (255, 255, 100)
    LABEL_PADDING = (8, 12)
    label_font = pygame.font.SysFont('Comic Sans MS', 20)

    metatile_coords_dict_filename = "metatile_coords_dict_" + str(LEVEL) + ".txt"
    f = open(metatile_coords_dict_filename, 'r')
    metatile_to_coords_dict = eval(f.readline())
    f.close()

    metatile_labels = []
    metatile_count = 0
    for metatile in metatile_to_coords_dict.keys():
        metatile_count += 1
        label_surface = label_font.render(str(metatile_count), False, FONT_COLOR)
        for coord in metatile_to_coords_dict[metatile]:
            metatile_labels.append((label_surface, coord[0], coord[1]))


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

    platform_list.draw(world)  # draw platforms tiles

    if not DRAW_METATILE_LABELS:
        player_list.draw(world)  # draw player
        goal_list.draw(world)  # draw goal tiles

    if DRAW_METATILE_LABELS:
        for coord in level.get_all_possible_coords(TILE):
            pygame.draw.rect(world, FONT_COLOR, (coord[0], coord[1], TILE, TILE), 1)

        for label in metatile_labels:
            surface, label_x, label_y = label
            world.blit(surface, (label_x + LABEL_PADDING[0], label_y + LABEL_PADDING[1]))

    pygame.display.flip()
    clock.tick(FPS)
