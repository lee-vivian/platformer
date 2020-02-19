"""'
Level Object
"""

import pygame
import tile

PIZZA_ALPHA = (255, 255, 255)


class Level:

    def get_border_coords(self, world_x, world_y, tile_dim):
        border_coords = []
        for xpos in range(int(world_x / tile_dim)):
            border_coords.append((xpos * tile_dim, 0))
            border_coords.append((xpos * tile_dim, world_y - tile_dim))
        for ypos in range(int(world_y / tile_dim)):
            border_coords.append((0, ypos * tile_dim))
            border_coords.append((world_x - tile_dim, ypos * tile_dim))
        return border_coords

    def get_platform_coords(self, lvl):
        platform_coords = []
        if lvl == 0:
            platform_coords += [
                (120, 120), (160, 120),
                (160, 80)
            ]
        elif lvl == 1:
            platform_coords += [
                (0, 400), (40, 400), (80, 400), (120, 400),
                (240, 320), (280, 320), (320, 320),
                (120, 600), (160, 600), (200, 600),
                (400, 240), (440, 240), (480, 240),
                (480, 120), (520, 120), (560, 120),
                (280, 560), (320, 560), (360, 560),
                (400, 400), (400, 440), (400, 480), (400, 520), (400, 560), (400, 600), (400, 640),
                (520, 360), (560, 360),
                (160, 480),
                (640, 280),
                (720, 200), (760, 200),
                (840, 160), (880, 160),
                (800, 280), (840, 280), (880, 280),
                (720, 360), (760, 360), (800, 360), (840, 360), (880, 360),
                (560, 440), (600, 440),
                (560, 480), (600, 480), (640, 480),
                (560, 520), (600, 520), (640, 520), (680, 520),
                (560, 560), (600, 560), (640, 560), (680, 560), (720, 560),
                (560, 600), (600, 600), (640, 600), (680, 600), (720, 600), (760, 600),
                (560, 640), (600, 640), (640, 640), (680, 640), (720, 640), (760, 640), (800, 640)]
        else:
            print("Level " + str(lvl))
        return platform_coords

    def platform(self, lvl, tile_dim, world_x, world_y):
        platform_list = pygame.sprite.Group()
        platform_coords = self.get_border_coords(world_x, world_y, tile_dim) + self.get_platform_coords(lvl)
        for (x, y) in platform_coords:
            platform = tile.Tile(x, y, 'tile.png')
            platform_list.add(platform)
        return platform_list

    def goal(self, lvl):
        goal_list = pygame.sprite.Group()
        if lvl == 0:
            goal = tile.Tile(160, 40, 'pizza.png', PIZZA_ALPHA)
            goal_list.add(goal)
        elif lvl == 1:
            goal = tile.Tile(880, 120, 'pizza.png', PIZZA_ALPHA)
            goal_list.add(goal)
        else:
            print("Level " + str(lvl))
        return goal_list

