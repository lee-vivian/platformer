'''
Basic Platform Game
author: Vivian Lee
created: 02-12-2020
acknowledgements: followed tutorial from opensource.com
'''

import pygame
import sys
import networkx as nx

import player
from tile import Tile
from model.level import TILE_DIM, MAX_WIDTH, MAX_HEIGHT
from model.level import Level
from model.action import Action
from camera import Camera

'''
Setup
'''

GAME = "sample"
LEVEL = "sample_hallway.txt"
# GAME = "kid_icarus"
# LEVEL = "kidicarus_1.txt"
# GAME = "super_mario_bros"
# LEVEL = "mario-4-1.txt"

USE_GRAPH = False
DRAW_METATILE_LABELS = False
DRAW_DUPLICATE_METATILES_ONLY = False

PLAYER_IMG = player.PLAYER_IMG
PIZZA_ALPHA = (255, 255, 255)


# Create level
level = Level.generate_level_from_file(GAME + "/" + LEVEL)

# Saved level filepaths
level_saved_files_dir = "level_saved_files_" + PLAYER_IMG + "/"
graph_file_path = level_saved_files_dir + "enumerated_state_graphs/graph_" + str(LEVEL) + ".gpickle"
metatile_coords_dict_filepath = level_saved_files_dir + "metatile_coords_dicts/metatile_coords_dict_" + str(LEVEL) + ".txt"

# Use precomputed graph
precomputed_graph = None if not USE_GRAPH else nx.read_gpickle(graph_file_path)
edge_actions_dict = None if not USE_GRAPH else nx.get_edge_attributes(precomputed_graph, "action")

# Background
FPS = 40  # frame rate
ANI = 4  # animation cycles
WORLD_X = min(level.width, MAX_WIDTH)
WORLD_Y = min(level.height, MAX_HEIGHT)
clock = pygame.time.Clock()
pygame.init()
world = pygame.display.set_mode([WORLD_X, WORLD_Y])
BACKGROUND_COLOR = (23, 23, 23)
# backdrop = pygame.image.load(os.path.join('images', 'platform_bkgd.png')).convert()
# backdropbox = world.get_rect()

# Player
player = player.Player()
player.reset()
player_list = pygame.sprite.Group()
player_list.add(player)

# Level
platform_list = pygame.sprite.Group()
for (x, y) in level.platform_coords:
    platform_list.add(Tile(x, y, 'tile.png'))

goal_list = pygame.sprite.Group()
for (x, y) in level.goal_coords:
    goal_list.add(Tile(x, y, 'pizza.png', PIZZA_ALPHA))

# Camera
camera = Camera(Camera.camera_function, level.width, level.height, WORLD_X, WORLD_Y)


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

    world.fill(BACKGROUND_COLOR)
    camera.update(player)  # set camera to track player
    player.update(Action(key_left, key_right, key_jump), platform_list, goal_list, precomputed_graph, edge_actions_dict)
    key_jump = False

    entities_to_draw = []
    entities_to_draw += list(platform_list) # draw platforms tiles
    entities_to_draw += list(player_list)  # draw player
    entities_to_draw += list(goal_list)  # draw goal tiles

    for e in entities_to_draw:
        world.blit(e.image, camera.apply(e))

    if DRAW_METATILE_LABELS:
        for coord in level.get_all_possible_coords():
            tile_rect = pygame.Rect(coord[0], coord[1], TILE_DIM, TILE_DIM)
            tile_rect = camera.apply_to_rect(pygame.Rect(coord[0], coord[1], TILE_DIM, TILE_DIM))  # adjust based on camera
            pygame.draw.rect(world, FONT_COLOR, tile_rect, 1)

        for label in metatile_labels:
            surface, label_x, label_y = label
            label_x, label_y = camera.apply_to_coord((label_x, label_y))
            world.blit(surface, (label_x + LABEL_PADDING[0], label_y + LABEL_PADDING[1]))

    pygame.display.flip()
    clock.tick(FPS)
