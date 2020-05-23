"""
Basic Platform Game
author: Vivian Lee
created: 02-12-2020
acknowledgements: followed tutorial from opensource.com
"""

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
from utils import read_pickle, error_exit, shortest_path_xy

COLORS = {
    'YELLOW': (255, 255, 100),
    'DARK_GRAY': (23, 23, 23),
    'GREEN': (48, 179, 55),
    'BLUE': (60, 145, 230),
    'RED': (237, 33, 14)
}

# game specifics
if os.getenv('MAZE'):
    print('***** USING MAZE RULES *****')
    from model_maze.player import PlayerMaze as Player
    from model_maze.inputs import InputsMaze as Inputs
else:
    print('***** USING PLATFORMER RULES *****')
    from model_platformer.player import PlayerPlatformer as Player
    from model_platformer.inputs import InputsPlatformer as Inputs


def get_text_label(text, font_size, font_color):
    label_font = pygame.font.SysFont('Comic Sans MS', font_size)
    score_label = label_font.render(text, False, font_color)
    return score_label


def get_label_rect_pairs(center_x, labels):
    label_rect_pairs = []
    stacked_label_height = 0
    for text, font_size, font_color in labels:
        label = get_text_label(text, font_size, font_color)
        label_rect = label.get_rect(center=(center_x, stacked_label_height + label.get_rect().height/2))
        stacked_label_height += label_rect.height
        label_rect_pairs.append((label, label_rect))
    return label_rect_pairs

def get_metatile_labels_at_coords(coords, tile_id, extra_info, label_font, font_color): #, graph_is_empty, font, color):
    new_labels = []
    label_text = tile_id[1:] + extra_info
    label_surface = label_font.render(label_text, False, font_color)
    for coord in coords:
        new_labels.append((label_surface, coord[0], coord[1]))
    return new_labels


def setup_metatile_labels(game, level, player_img, draw_all_labels, draw_dup_labels):
    metatile_labels = []
    font_color = COLORS.get('YELLOW')
    label_padding = (8, 12)
    label_font = pygame.font.SysFont('Comic Sans MS', 20)

    tile_id_coords_map_filepath = "level_saved_files_%s/tile_id_coords_maps/%s/%s.pickle" % (player_img, game, level)
    tile_id_coords_map = read_pickle(tile_id_coords_map_filepath)

    for (tile_id, extra_info), coords in tile_id_coords_map.items():

        if (draw_dup_labels and len(coords) > 1) or draw_all_labels:

            metatile_labels += get_metatile_labels_at_coords(coords, tile_id, extra_info, label_font, font_color)

    return metatile_labels, font_color, label_padding


def get_sprites(coords, img):
    sprites = pygame.sprite.Group()
    for (x, y) in coords:
        sprites.add(Tile(x, y, img))
    return sprites


def main(game, level, player_img, use_graph, draw_all_labels, draw_dup_labels, draw_path, show_score):

    # Create the Level
    level_obj = Level.generate_level_from_file(game, level)

    # Level saved files
    state_graph_file = "level_saved_files_%s/enumerated_state_graphs/%s/%s.gpickle" % (player_img, game, level)

    if game == "generated" and os.path.exists("level_saved_files_%s/generated_level_paths/%s.pickle" % (player_img, level)):
        generated_level_path_coords = read_pickle("level_saved_files_%s/generated_level_paths/%s.pickle" % (player_img, level))
    else:
        generated_level_path_coords = None

    if use_graph and os.path.exists(state_graph_file):
        print("***** USING ENUMERATED STATE GRAPH *****")
        state_graph = nx.read_gpickle(state_graph_file)
    else:
        print("***** USING MANUAL CONTROLS *****")
        state_graph = None

    edge_actions_dict = None if state_graph is None else nx.get_edge_attributes(state_graph, 'action')

    # Background
    FPS = 40  # frame rate
    ANI = 4  # animation cycles
    WORLD_X = min(level_obj.width, MAX_WIDTH)
    WORLD_Y = min(level_obj.height, MAX_HEIGHT)
    clock = pygame.time.Clock()
    pygame.init()
    world = pygame.display.set_mode([WORLD_X, WORLD_Y])
    BACKGROUND_COLOR = COLORS.get('DARK_GRAY')

    # Player
    player_model = Player(player_img, level_obj)
    player_view = PlayerView(player_img)
    player_list = pygame.sprite.Group()
    player_list.add(player_view)

    # Level
    platform_sprites = get_sprites(level_obj.get_platform_coords(), 'block_tile.png')
    goal_sprites = get_sprites(level_obj.get_goal_coords(), 'goal_tile.png')
    bonus_sprites = get_sprites(level_obj.get_bonus_coords(), 'bonus_tile.png')
    one_way_platform_sprites = get_sprites(level_obj.get_one_way_platform_coords(), 'one_way_block_tile.png')
    hazard_sprites = get_sprites(level_obj.get_hazard_coords(), 'hazard_tile.png')
    collected_bonus_tile_coords_dict = {}

    # Camera
    camera = Camera(Camera.camera_function, level_obj.width, level_obj.height, WORLD_X, WORLD_Y)

    # Setup drawing metatile labels
    if draw_all_labels or draw_dup_labels:
        metatile_labels, font_color, label_padding = \
            setup_metatile_labels(game, level, player_img, draw_all_labels, draw_dup_labels)

    # Setup drawing solution path
    if draw_path:
        path_font_color = COLORS.get('GREEN')
        start_font_color = COLORS.get('BLUE')
        goal_font_color = COLORS.get('RED')

        if generated_level_path_coords is not None:
            path_coords = generated_level_path_coords
            start_coord = generated_level_path_coords[0]
            goal_coord = generated_level_path_coords[-1]

        elif os.path.exists(state_graph_file):
            graph = nx.read_gpickle(state_graph_file)
            shortest_path_dict = shortest_path_xy(graph)
            path_coords = shortest_path_dict.get("path_coords")
            start_coord = shortest_path_dict.get("start_coord")
            goal_coord = shortest_path_dict.get("goal_coord")

        else:
            error_exit("No enumeratd state graph available to draw solution path")

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
                    collected_bonus_tile_coords_dict = {}
                    platform_sprites = get_sprites(level_obj.get_platform_coords(), 'block_tile.png')

            input_handler.onEvent(event)

        if not main:
            break

        world.fill(BACKGROUND_COLOR)
        camera.update(player_view)  # set camera to track player

        # Update Player model and view
        player_model.update(action=input_handler.getAction(),
                            precomputed_graph=state_graph, edge_actions_dict=edge_actions_dict)

        player_view.update(player_model.state.x, player_model.state.y,
                           player_model.half_player_w, player_model.half_player_h)

        # Update the current score
        hit_bonus_coord = player_model.get_hit_bonus_coord()

        if hit_bonus_coord is not None and collected_bonus_tile_coords_dict.get(hit_bonus_coord) is None:
            collected_bonus_tile_coords_dict[hit_bonus_coord] = 1
            platform_sprites.add(Tile(hit_bonus_coord[0], hit_bonus_coord[1], 'block_tile.png'))

        score = len(collected_bonus_tile_coords_dict) * 10

        # Draw sprites
        entities_to_draw = []
        entities_to_draw += list(bonus_sprites)  # draw bonus tiles
        entities_to_draw += list(platform_sprites)  # draw platforms tiles
        entities_to_draw += list(one_way_platform_sprites)  # draw one-way platform tiles
        entities_to_draw += list(hazard_sprites)
        entities_to_draw += list(player_list)  # draw player
        entities_to_draw += list(goal_sprites)  # draw goal tiles

        for e in entities_to_draw:
            world.blit(e.image, camera.apply(e))

        # Draw metatile labels
        if draw_all_labels or draw_dup_labels:
            for coord in level_obj.get_all_possible_coords():  # draw metatile border outlines
                tile_rect = pygame.Rect(coord[0], coord[1], TILE_DIM, TILE_DIM)
                tile_rect = camera.apply_to_rect(tile_rect)  # adjust based on camera
                pygame.draw.rect(world, font_color, tile_rect, 1)

            for label in metatile_labels:  # draw metatile labels
                surface, label_x, label_y = label
                label_x, label_y = camera.apply_to_coord((label_x, label_y))
                world.blit(surface, (label_x + label_padding[0], label_y + label_padding[1]))

        # Draw level solution path
        if draw_path:
            for coord in path_coords:
                if coord == start_coord:
                    color = start_font_color
                elif coord == goal_coord:
                    color = goal_font_color
                else:
                    color = path_font_color
                coord = eval(coord)
                path_component = pygame.Rect(coord[0], coord[1], 2, 2)
                path_component = camera.apply_to_rect(path_component)
                pygame.draw.rect(world, color, path_component, 1)

        # Draw text labels
        label_rect_pairs = []
        if player_model.goal_reached():
            score += 50
            labels = [
                ("You Win!", 50, COLORS.get('GREEN')),
                ("Score: %d" % score, 30, COLORS.get('YELLOW')),
                ("Press 'R' to replay or 'Q' to quit", 30, COLORS.get('YELLOW'))
            ]
            label_rect_pairs = get_label_rect_pairs(center_x=WORLD_X/2, labels=labels)

        elif player_model.is_dead():
            labels = [
                ("Game Over", 50, COLORS.get('RED')),
                ("Score: %d" % score, 30, COLORS.get('YELLOW')),
                ("Press 'R' to replay or 'Q' to quit", 30, COLORS.get('YELLOW'))
            ]
            label_rect_pairs = get_label_rect_pairs(center_x=WORLD_X / 2, labels=labels)

        elif show_score:
            labels = [("Score: %d" % score, 50, COLORS.get('YELLOW'))]
            label_rect_pairs = get_label_rect_pairs(center_x=WORLD_X / 2, labels=labels)

        for label, label_rect in label_rect_pairs:
            world.blit(label, label_rect)

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
    parser.add_argument('--draw_path', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--show_score', const=True, nargs='?', type=bool, default=False)
    args = parser.parse_args()

    main(args.game, args.level, args.player_img, args.use_graph, args.draw_all_labels, args.draw_dup_labels,
         args.draw_path, args.show_score)
