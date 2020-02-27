"""'
Level Object
"""

import pygame
import tile

TILE = 40
MAX_WORLD_X = 960
MAX_WORLD_Y = 720
PIZZA_ALPHA = (255, 255, 255)


class Level:

    def __init__(self, lvl):
        self.lvl = lvl
        self.world_x = self.get_world_xy(lvl)[0]
        self.world_y = self.get_world_xy(lvl)[1]

    def get_world_xy(self, lvl):
        if lvl == 0:
            return (240, 200)
        elif lvl == 2:
            return (800, 160)
        elif lvl == 3:
            return (320, 320)
        elif lvl == 5:
            return (1000, 160)
        else:
            return (MAX_WORLD_X, MAX_WORLD_Y)

    def get_all_possible_coords(self):
        coords = []
        for x in range(int(self.world_x / TILE)):
            for y in range(int(self.world_y / TILE)):
                coords.append((x * TILE, y * TILE))

        return coords

    def get_border_coords(self):
        border_coords = []
        for xpos in range(int(self.world_x / TILE)):
            border_coords.append((xpos * TILE, 0))
            border_coords.append((xpos * TILE, self.world_y - TILE))
        for ypos in range(int(self.world_y / TILE)):
            border_coords.append((0, ypos * TILE))
            border_coords.append((self.world_x - TILE, ypos * TILE))

        return border_coords

    def get_goal_coords(self):
        goal_coords = []
        if self.lvl == 0:
            goal_coords += [(160, 40)]
        elif self.lvl == 1:
            goal_coords += [(880, 120)]
        elif self.lvl == 2:
            goal_coords += [(720, 80)]
        elif self.lvl == 3:
            goal_coords += [(240, 160)]
        elif self.lvl == 4:
            goal_coords += [(880, 240)]
        elif self.lvl == 5:
            goal_coords += [(920, 80)]

        return goal_coords

    def get_platform_coords(self):
        platform_coords = []
        if self.lvl == 0:
            platform_coords += [
                (120, 120), (160, 120),
                (160, 80)
            ]
        elif self.lvl in [1, 4]:
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
        elif self.lvl == 3:
            platform_coords += [
                (200, 200), (240, 200)
            ]

        return platform_coords

    def platform(self):
        platform_list = pygame.sprite.Group()
        platform_coords = self.get_border_coords() + self.get_platform_coords()
        for (x, y) in platform_coords:
            platform = tile.Tile(x, y, 'tile.png')
            platform_list.add(platform)
        return platform_list

    def goal(self):
        goal_list = pygame.sprite.Group()
        goal_coords = self.get_goal_coords()
        for (x, y) in goal_coords:
            goal = tile.Tile(x, y, 'pizza.png', PIZZA_ALPHA)
            goal_list.add(goal)
        return goal_list


