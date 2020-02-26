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
# from metatile import Metatile

'''
Setup
'''

LEVEL = 1
USE_GRAPH = True
DRAW_METATILE_LABELS = True
DRAW_DUPLICATE_METATILES_ONLY = True

# Create level
level = level.Level(LEVEL)

# Saved level filepaths
graph_file_path = "level_saved_files/enumerated_state_graphs/graph_" + str(LEVEL) + ".gpickle"
metatile_coords_dict_filepath = "level_saved_files/metatile_coords_dicts/metatile_coords_dict_" + str(LEVEL) + ".txt"

# Use precomputed graph
precomputed_graph = None if not USE_GRAPH else nx.read_gpickle(graph_file_path)
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


def get_metatile_labels_at_coords(coords, count, font, color):
    new_labels = []
    label_surface = font.render(str(count), False, color)
    for coord in coords:
        new_labels.append((label_surface, coord[0], coord[1]))
    return new_labels


if DRAW_METATILE_LABELS:

    FONT_COLOR = (255, 255, 100)
    LABEL_PADDING = (8, 12)
    LABEL_FONT = pygame.font.SysFont('Comic Sans MS', 20)

    f = open(metatile_coords_dict_filepath, 'r')
    metatile_to_coords_dict = eval(f.readline())
    f.close()

    metatile_labels = []
    metatile_count = 0

    for metatile in metatile_to_coords_dict.keys():

        coords = metatile_to_coords_dict[metatile]

        if DRAW_DUPLICATE_METATILES_ONLY:
            if len(coords) > 1:
                metatile_count += 1
                metatile_labels += get_metatile_labels_at_coords(coords, metatile_count, LABEL_FONT, FONT_COLOR)
        else:
            metatile_count += 1
            metatile_labels += get_metatile_labels_at_coords(coords, metatile_count, LABEL_FONT, FONT_COLOR)

    # if LEVEL == 1:
    #     keys = list(metatile_to_coords_dict.keys())
    #     print(keys[0])  # gray block
    #     print(keys[213])  # pizza tile
    #     gray_block_metatile = Metatile.from_str(keys[0])
    #     pizza_metatile = Metatile.from_str(keys[213])
    #     print(gray_block_metatile == pizza_metatile)


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
