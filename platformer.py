'''
Basic Platform Game
author: Vivian Lee
created: 02-12-2020
acknowledgements: followed tutorial from opensource.com
'''

import pygame
import os
import sys
import networkx as nx
import argparse

from view.player import Player as PlayerView
from view.tile import Tile
from view.camera import Camera
from model.level import TILE_DIM, MAX_WIDTH, MAX_HEIGHT
from model.level import Level
from utils import read_pickle

# game specifics
if os.getenv('MAZE'):
    from model_maze.player import PlayerMaze as Player
    from model_maze.inputs import InputsMaze as Inputs
else:
    from model_platformer.player import PlayerPlatformer as Player
    from model_platformer.inputs import InputsPlatformer as Inputs


def get_metatile_labels_at_coords(coords, tile_id, extra_info, label_font, font_color): #, graph_is_empty, font, color):
    new_labels = []
    label_text = tile_id[1:] + extra_info
    label_surface = label_font.render(label_text, False, font_color)
    for coord in coords:
        new_labels.append((label_surface, coord[0], coord[1]))
    return new_labels


def setup_metatile_labels(level, player_img, draw_all_labels, draw_dup_labels):
    metatile_labels = []
    font_color = (255, 255, 100)
    label_padding = (8, 12)
    label_font = pygame.font.SysFont('Comic Sans MS', 20)

    tile_id_coords_map_filepath = "level_saved_files_%s/tile_id_coords_maps/%s.pickle" % (player_img, level)
    tile_id_coords_map = read_pickle(tile_id_coords_map_filepath)

    for (tile_id, extra_info), coords in tile_id_coords_map.items():

        if (draw_dup_labels and len(coords) > 1) or draw_all_labels:

            metatile_labels += get_metatile_labels_at_coords(coords, tile_id, extra_info, label_font, font_color)

    return metatile_labels, font_color, label_padding


def main(game, level, player_img, use_graph, draw_all_labels, draw_dup_labels):

    # Create the Level
    level_obj = Level.generate_level_from_file("%s/%s.txt" % (game, level))

    # Level saved files
    level_saved_files_dir = "level_saved_files_%s/" % player_img
    state_graph_file = level_saved_files_dir + "enumerated_state_graphs/%s/%s.gpickle" % (game, level)
    metatile_coords_dict_file = level_saved_files_dir + "metatile_coords_dicts/%s/%s.pickle" % (game, level)
    metatile_id_map_file = level_saved_files_dir + "metatile_id_maps/%s.pickle" % level

    state_graph = None if not use_graph else nx.read_gpickle(state_graph_file)
    edge_actions_dict = None if not use_graph else nx.get_edge_attributes(state_graph, 'action')

    # Background
    FPS = 40  # frame rate
    ANI = 4  # animation cycles
    WORLD_X = min(level_obj.width, MAX_WIDTH)
    WORLD_Y = min(level_obj.height, MAX_HEIGHT)
    clock = pygame.time.Clock()
    pygame.init()
    world = pygame.display.set_mode([WORLD_X, WORLD_Y])
    BACKGROUND_COLOR = (23, 23, 23)

    # Player
    player_model = Player(player_img, level_obj.start_coord)
    player_view = PlayerView(player_img)
    player_list = pygame.sprite.Group()
    player_list.add(player_view)

    # Level
    platform_list = pygame.sprite.Group()
    for (x, y) in level_obj.platform_coords:
        platform_list.add(Tile(x, y, 'gray_tile.png'))

    goal_list = pygame.sprite.Group()
    for (x, y) in level_obj.goal_coords:
        goal_list.add(Tile(x, y, 'pizza.png'))

    # Camera
    camera = Camera(Camera.camera_function, level_obj.width, level_obj.height, WORLD_X, WORLD_Y)

    # Setup drawing metatile labels
    if draw_all_labels or draw_dup_labels:
        metatile_labels, font_color, label_padding = \
            setup_metatile_labels(level, player_img, draw_all_labels, draw_dup_labels)

    # Input handling
    input_handler = Inputs()

    # Main Loop
    main = True

    while main:
        input_handler.onLoop()
        
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
                    player_model.reset()

            input_handler.onEvent(event)

        world.fill(BACKGROUND_COLOR)
        camera.update(player_view)  # set camera to track player

        player_model.update(input_handler.getAction(), level_obj.platform_coords, level_obj.goal_coords,
                            state_graph, edge_actions_dict)
        player_view.update(player_model.state.x, player_model.state.y,
                           player_model.half_player_w, player_model.half_player_h)

        entities_to_draw = []
        entities_to_draw += list(platform_list) # draw platforms tiles
        entities_to_draw += list(player_list)  # draw player
        entities_to_draw += list(goal_list)  # draw goal tiles

        for e in entities_to_draw:
            world.blit(e.image, camera.apply(e))

        if draw_all_labels or draw_dup_labels:
            for coord in level_obj.get_all_possible_coords():  # draw metatile border outlines
                tile_rect = pygame.Rect(coord[0], coord[1], TILE_DIM, TILE_DIM)
                tile_rect = camera.apply_to_rect(tile_rect)  # adjust based on camera
                pygame.draw.rect(world, font_color, tile_rect, 1)

            for label in metatile_labels:  # draw metatile labels
                surface, label_x, label_y = label
                label_x, label_y = camera.apply_to_coord((label_x, label_y))
                world.blit(surface, (label_x + label_padding[0], label_y + label_padding[1]))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Play platformer game')
    parser.add_argument('game', type=str, help='The game to play')
    parser.add_argument('level', type=str, help='The game level to play')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--use_graph', const=True, nargs='?', type=bool, help='Use the level enumerated state graph', default=False)
    parser.add_argument('--draw_all_labels', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--draw_dup_labels', const=True, nargs='?', type=bool, default=False)
    args = parser.parse_args()

    main(args.game, args.level, args.player_img, args.use_graph, args.draw_all_labels, args.draw_dup_labels)
