'''
Reads in the saved tiles from the constraint solver and displays the level image and metatile labels
'''

import pygame
import sys
import argparse

from model.player import Player as PlayerModel
from model.metatile import Metatile, TYPE_IMG_MAP
from model.action import Action
from view.player import Player as PlayerView
from view.tile import Tile
from view.camera import Camera
from model.level import TILE_DIM, MAX_WIDTH, MAX_HEIGHT
from utils import read_pickle


def get_metatile_labels(coord_id_map, coord_metatile_map):
    font_color = (255, 255, 100)
    label_padding = (8, 12)
    label_font = pygame.font.SysFont('Comic Sans MS', 20)

    metatile_labels = []

    for coord, id in coord_id_map.items():
        metatile_label = id[1:]  # remove t-prefix from metatile id
        metatile = coord_metatile_map.get(coord)
        graph_is_empty = not bool(metatile.graph_as_dict)
        if graph_is_empty:
            metatile_label += "E"
        label_surface = label_font.render(metatile_label, False, font_color)
        metatile_labels.append((label_surface, coord[0], coord[1]))
    return metatile_labels, font_color, label_padding


def main(level, player_img='block', draw_labels=True):

    saved_tiles_file = "../groundcollapse/chunks/%s/chunk_0_0" % level
    saved_tiles_rows = read_pickle(saved_tiles_file)  # list of lists (each list represents 1 tile row)

    id_metatile_map_file = "level_saved_files_%s/id_metatile_maps/%s.pickle" % (player_img, level)
    id_metatile_map = read_pickle(id_metatile_map_file)

    num_rows = len(saved_tiles_rows)
    num_cols = len(saved_tiles_rows[0])

    coord_id_map = {}
    for r in range(num_rows):
        for c in range(num_cols):
            coord = (r * TILE_DIM, c * TILE_DIM)
            id = saved_tiles_rows[r][c]
            coord_id_map[coord] = id

    coord_metatile_map = {}
    for coord, id in coord_id_map.items():
        metatile = Metatile.from_str(id_metatile_map.get(id))
        coord_metatile_map[coord] = metatile

    # Background
    FPS = 40  # frame rate
    level_w = num_cols * TILE_DIM
    level_h = num_rows * TILE_DIM
    WORLD_X = min(level_w, MAX_WIDTH)
    WORLD_Y = min(level_h, MAX_HEIGHT)
    clock = pygame.time.Clock()
    pygame.init()
    world = pygame.display.set_mode([WORLD_X, WORLD_Y])
    BACKGROUND_COLOR = (23, 23, 23)

    platform_coords = []
    goal_coords = []
    start_coord = None
    blank_coord = None
    tiles_list = pygame.sprite.Group()

    for coord, metatile in coord_metatile_map.items():
        if start_coord is None and metatile.type == 'start':
            start_coord = coord
        if blank_coord is None and metatile.type == 'blank':
            blank_coord = coord
        if metatile.type == 'block':
            platform_coords.append(coord)
        if metatile.type == 'goal':
            goal_coords.append(coord)
        tiles_list.add(Tile(coord[0], coord[1], TYPE_IMG_MAP.get(metatile.type)))  # get tile sprites

    player_start_coord = start_coord if start_coord is not None else blank_coord
    player_model = PlayerModel(player_img, player_start_coord)
    player_view = PlayerView(player_img)
    player_list = pygame.sprite.Group()
    player_list.add(player_view)  # get player sprite

    camera = Camera(Camera.camera_function, level_w, level_h, WORLD_X, WORLD_Y)  # setup camera

    # Setup drawing metatile labels
    if draw_labels:
        metatile_labels, font_color, label_padding = get_metatile_labels(coord_id_map, coord_metatile_map)

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
        player_model.update(Action(key_left, key_right, key_jump), platform_coords, goal_coords)
        player_view.update(player_model.state.x, player_model.state.y,
                           player_model.half_player_w, player_model.half_player_h, player_model.state.facing_right)
        key_jump = False

        entities_to_draw = []
        entities_to_draw += list(tiles_list)  # draw tiles
        entities_to_draw += list(player_list)  # draw player

        for e in entities_to_draw:
            world.blit(e.image, camera.apply(e))

        if draw_labels:
            for coord in list(coord_metatile_map.keys()):  # draw metatile border outlines
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
    parser.add_argument('level', type=str, help='Level name')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--draw_labels', type=bool, default=True)
    args = parser.parse_args()

    main(args.level, args.player_img, args.draw_labels)
