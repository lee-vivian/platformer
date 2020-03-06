'''
Basic Platform Game
author: Vivian Lee
created: 02-12-2020
acknowledgements: followed tutorial from opensource.com
'''

import pygame
import sys
import networkx as nx
import argparse

from view.player import Player as PlayerView
from view.tile import Tile
from view.camera import Camera
from model.player import Player as PlayerModel
from model.level import TILE_DIM, MAX_WIDTH, MAX_HEIGHT
from model.level import Level
from model.action import Action


def get_metatile_labels_at_coords(coords, count, graph_is_empty, font, color):
    new_labels = []
    label_text = str(count)
    if graph_is_empty:
        label_text += "E"
    label_surface = font.render(label_text, False, color)
    for coord in coords:
        new_labels.append((label_surface, coord[0], coord[1]))
    return new_labels


def setup_metatile_labels(metatile_coords_dict_file, draw_dup_labels_only=True):

    font_color = (255, 255, 100)
    label_padding = (8, 12)
    label_font = pygame.font.SysFont('Comic Sans MS', 20)

    f = open(metatile_coords_dict_file, 'r')
    metatile_coords_dict = eval(f.readline())
    f.close()

    metatile_labels = []
    metatile_count = 0

    for metatile_str in metatile_coords_dict.keys():
        coords = metatile_coords_dict.get(metatile_str)
        metatile = eval(metatile_str)
        graph_is_empty = not bool(metatile.get('graph'))

        if draw_dup_labels_only:
            if len(coords) > 1:
                metatile_count += 1
                metatile_labels += get_metatile_labels_at_coords(coords, metatile_count, graph_is_empty, label_font, font_color)
        else:
            metatile_count += 1
            metatile_labels += get_metatile_labels_at_coords(coords, metatile_count, graph_is_empty, label_font, font_color)

    return metatile_labels, font_color, label_padding


def main(game, level, player_img, use_graph, draw_labels, draw_dup_labels_only):

    # Create the Level
    level = Level.generate_level_from_file("%s/%s.txt" % (game, level))

    # Level saved files
    level_saved_files_dir = "level_saved_files_%s/" % player_img
    state_graph_file = level_saved_files_dir + "enumerated_state_graphs/%s/%s.gpickle" % (game, level)
    metatile_coords_dict_file = level_saved_files_dir + "metatile_coords_dicts/%s/%s.pickle" % (game, level)

    state_graph = None if not use_graph else nx.read_gpickle(state_graph_file)
    edge_actions_dict = None if not use_graph else nx.get_edge_attributes(state_graph, 'action')

    # Background
    FPS = 40  # frame rate
    ANI = 4  # animation cycles
    WORLD_X = min(level.width, MAX_WIDTH)
    WORLD_Y = min(level.height, MAX_HEIGHT)
    clock = pygame.time.Clock()
    pygame.init()
    world = pygame.display.set_mode([WORLD_X, WORLD_Y])
    BACKGROUND_COLOR = (23, 23, 23)

    # Player
    player_model = PlayerModel(player_img, level.start_coord)
    player_view = PlayerView(player_img)
    player_list = pygame.sprite.Group()
    player_list.add(player_view)

    # Level
    platform_list = pygame.sprite.Group()
    for (x, y) in level.platform_coords:
        platform_list.add(Tile(x, y, 'gray_tile.png'))

    goal_list = pygame.sprite.Group()
    for (x, y) in level.goal_coords:
        goal_list.add(Tile(x, y, 'pizza.png'))

    # Camera
    camera = Camera(Camera.camera_function, level.width, level.height, WORLD_X, WORLD_Y)

    # Setup drawing metatile labels
    if draw_labels:
        metatile_labels, font_color, label_padding = setup_metatile_labels(metatile_coords_dict_file, draw_dup_labels_only)

    # Main Loop
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
                    player_model.reset()
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
        camera.update(player_view)  # set camera to track player
        player_model.update(Action(key_left, key_right, key_jump), level.platform_coords, level.goal_coords,
                            state_graph, edge_actions_dict)
        player_view.update(player_model.state.x, player_model.state.y,
                           player_model.half_player_w, player_model.half_player_h, player_model.state.facing_right)
        key_jump = False

        entities_to_draw = []
        entities_to_draw += list(platform_list) # draw platforms tiles
        entities_to_draw += list(player_list)  # draw player
        entities_to_draw += list(goal_list)  # draw goal tiles

        for e in entities_to_draw:
            world.blit(e.image, camera.apply(e))

        if draw_labels:
            for coord in level.get_all_possible_coords():
                tile_rect = pygame.Rect(coord[0], coord[1], TILE_DIM, TILE_DIM)
                tile_rect = camera.apply_to_rect(tile_rect)  # adjust based on camera
                pygame.draw.rect(world, font_color, tile_rect, 1)

            for label in metatile_labels:
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
    parser.add_argument('--use_graph', type=bool, help='Use the level enumerated state graph', default=False)
    parser.add_argument('--draw_labels', type=bool, help='Draw the metatile labels', default=False)
    parser.add_argument('--draw_dup_labels_only', type=bool, help='Draw duplicate metatile labels only', default=True)
    args = parser.parse_args()

    main(args.game, args.level, args.player_img, args.use_graph, args.draw_labels, args.draw_dup_labels_only)
