''''
Level Object
'''

import pygame
import tile


class Level:
    @staticmethod
    def ground(lvl, world_x, world_y, tile_dim):
        ground_list = pygame.sprite.Group()
        if lvl == 1:
            temp = int(world_x / tile_dim)
            for xpos in range(int(world_x / tile_dim)):
                ground = tile.Tile(xpos * tile_dim, world_y - tile_dim, tile_dim, tile_dim, 'tile.png')
                ground_list.add(ground)
        else:
            print("Level " + str(lvl))

        return ground_list

    @staticmethod
    def platform(lvl, tile_dim):
        platform_list = pygame.sprite.Group()
        if lvl == 1:
            platform_locs = [
                (0, 400), (40, 400), (80, 400), (120, 400),
                (200, 320), (240, 320), (280, 320), (320, 320),
                (120, 520), (160, 520), (200, 520), (240, 520),
                (400, 240), (440, 240), (480, 240),
                (480, 120), (520, 120), (560, 120),
                (400, 400), (400, 440), (400, 480), (400, 520), (400, 560), (400, 600), (400, 640),
                (600, 320), (640, 320),
                (720, 200), (760, 200),
                (840, 120), (880, 120), (920, 120),
                (840, 280), (880, 280), (920, 280),
                (720, 360), (760, 360), (800, 360), (840, 360), (880, 360),
                (560, 440), (600, 440),
                (560, 480), (600, 480), (640, 480),
                (560, 520), (600, 520), (640, 520), (680, 520),
                (560, 560), (600, 560), (640, 560), (680, 560), (720, 560),
                (560, 600), (600, 600), (640, 600), (680, 600), (720, 600), (760, 600),
                (560, 640), (600, 640), (640, 640), (680, 640), (720, 640), (760, 640), (800, 640)]

            for (x, y) in platform_locs:
                platform = tile.Tile(x, y, tile_dim, tile_dim, 'tile.png')
                platform_list.add(platform)
        else:
            print("Level " + str(lvl))

        return platform_list
