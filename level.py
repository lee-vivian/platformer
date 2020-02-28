"""'
Level Object
"""

TILE_DIM = 40
TILE_CHARS = ['#', '?', 'B']
GOAL_CHARS = ['*']

MAX_WIDTH = 1200
MAX_HEIGHT = 360

LEVEL_STRUCTURES_DIR = "level_structural_layers/"


class Level:

    def __init__(self, name, width, height, platform_coords, goal_coords):
        self.name = name
        self.width = width
        self.height = height
        self.platform_coords = platform_coords
        self.goal_coords = goal_coords

    def get_all_possible_coords(self):
        coords = []
        for x in range(int(self.width / TILE_DIM)):
            for y in range(int(self.height / TILE_DIM)):
                coords.append((x * TILE_DIM, y * TILE_DIM))
        return coords

    @staticmethod
    def generate_level_from_file(filepath):
        level_width = 0
        level_height = 0
        platform_coords = []
        goal_coords = []

        f = open(LEVEL_STRUCTURES_DIR + filepath, 'r')

        for line in f:

            # Setup
            if level_width == 0:
                level_width = len(line) + 2  # get level width + 2 for left and right border tiles
                for x in range(level_width):
                    platform_coords.append((x * TILE_DIM, level_height * TILE_DIM))  # add ceiling tiles
                level_height += 1

            # Parse line
            for char_index in range(level_width):

                char_coord = (char_index * TILE_DIM, level_height * TILE_DIM)

                if char_index in [0, level_width-1]:  # add left and right border tiles
                    platform_coords.append(char_coord)
                else:
                    print("char index: ", char_index - 1)
                    print("line len: ", len(line))
                    char = line[char_index - 1]
                    print(char_index - 1)
                    if char in TILE_CHARS:
                        platform_coords.append(char_coord)
                    elif char in GOAL_CHARS:
                        goal_coords.append(char_coord)

            level_height += 1

        f.close()

        return Level(filepath, level_width * TILE_DIM, level_height * TILE_DIM, platform_coords, goal_coords)


    # def get_world_xy(self, lvl):
    #     if lvl == 0:
    #         return (240, 200)
    #     elif lvl == 2:
    #         return (800, 160)
    #     elif lvl == 3:
    #         return (320, 320)
    #     elif lvl == 5:
    #         return (1000, 160)
    #     elif lvl == 6:
    #         return (2000, 1200)
    #     else:
    #         return (MAX_WORLD_X, MAX_WORLD_Y)


    # def get_border_coords(self):
    #     border_coords = []
    #     for xpos in range(int(self.width / TILE)):
    #         border_coords.append((xpos * TILE, 0))
    #         border_coords.append((xpos * TILE, self.height - TILE))
    #     for ypos in range(int(self.height / TILE)):
    #         border_coords.append((0, ypos * TILE))
    #         border_coords.append((self.width - TILE, ypos * TILE))
    #
    #     return border_coords
    #
    # def get_goal_coords(self):
    #     goal_coords = []
    #     if self.lvl == 0:
    #         goal_coords += [(160, 40)]
    #     elif self.lvl == 1:
    #         goal_coords += [(880, 120)]
    #     elif self.lvl == 2:
    #         goal_coords += [(720, 80)]
    #     elif self.lvl == 3:
    #         goal_coords += [(240, 160)]
    #     elif self.lvl == 4:
    #         goal_coords += [(880, 240)]
    #     elif self.lvl == 5:
    #         goal_coords += [(920, 80)]
    #     elif self.lvl == 6:
    #         goal_coords += [(1760, 240)]
    #
    #     return goal_coords
    #
    # def get_platform_coords(self):
    #     platform_coords = []
    #     if self.lvl == 0:
    #         platform_coords += [
    #             (120, 120), (160, 120),
    #             (160, 80)
    #         ]
    #     elif self.lvl in [1, 4]:
    #         platform_coords += [
    #             (0, 400), (40, 400), (80, 400), (120, 400),
    #             (240, 320), (280, 320), (320, 320),
    #             (120, 600), (160, 600), (200, 600),
    #             (400, 240), (440, 240), (480, 240),
    #             (480, 120), (520, 120), (560, 120),
    #             (280, 560), (320, 560), (360, 560),
    #             (400, 400), (400, 440), (400, 480), (400, 520), (400, 560), (400, 600), (400, 640),
    #             (520, 360), (560, 360),
    #             (160, 480),
    #             (640, 280),
    #             (720, 200), (760, 200),
    #             (840, 160), (880, 160),
    #             (800, 280), (840, 280), (880, 280),
    #             (720, 360), (760, 360), (800, 360), (840, 360), (880, 360),
    #             (560, 440), (600, 440),
    #             (560, 480), (600, 480), (640, 480),
    #             (560, 520), (600, 520), (640, 520), (680, 520),
    #             (560, 560), (600, 560), (640, 560), (680, 560), (720, 560),
    #             (560, 600), (600, 600), (640, 600), (680, 600), (720, 600), (760, 600),
    #             (560, 640), (600, 640), (640, 640), (680, 640), (720, 640), (760, 640), (800, 640)]
    #     elif self.lvl == 3:
    #         platform_coords += [
    #             (200, 200), (240, 200)
    #         ]
    #     elif self.lvl == 6:
    #         platform_coords += [
    #             (1, 5), (2, 5), (3, 5),
    #             (1, 22),
    #             (1, 25), (2, 25), (3, 25),
    #             (3, 20),
    #             (5, 7), (6, 7), (7, 7),
    #             (5, 18),
    #             (9, 5), (10, 5), (11, 5), (12, 5), (13, 5),
    #             (5, 22), (6, 22), (7, 22),
    #             (5, 27), (6, 27),
    #             (8, 9), (9, 9),
    #             (9, 10), (10, 10),
    #             (10, 11), (11, 11),
    #             (11, 12), (12, 12),
    #             (12, 10),
    #             (12, 16),
    #             (11, 17), (12, 17),
    #             (10, 18), (11, 18), (12, 18),
    #             (9, 19), (10, 19), (11, 19), (12, 19),
    #             (8, 20), (9, 20), (10, 20), (11, 20), (12, 20),
    #             (8, 21), (9, 21), (10, 21), (11, 21), (12, 21),
    #             (8, 22), (9, 22), (10, 22), (11, 22), (12, 22),
    #             (8, 23), (9, 23), (10, 23), (11, 23), (12, 23),
    #             (8, 24), (9, 24), (10, 24), (11, 24), (12, 24),
    #             (8, 25), (9, 25), (10, 25), (11, 25), (12, 25),
    #             (8, 26), (9, 26), (10, 26), (11, 26), (12, 26),
    #             (8, 27), (9, 27), (10, 27), (11, 27), (12, 27),
    #             (8, 28), (9, 28), (10, 28), (11, 28), (12, 28),
    #             (15, 12), (16, 12), (17, 12),
    #             (15, 16), (15, 17), (15, 18), (15, 19), (15, 20),
    #             (15, 21), (15, 22), (15, 23), (15, 24), (15, 25),
    #             (15, 26), (15, 27), (15, 28),
    #             (16, 21), (17, 21), (18, 21), (19, 21),
    #             (19, 17), (19, 18), (19, 19), (19, 20),
    #             (19, 10), (20, 10),
    #             (22, 8), (24, 6), (27, 5), (30, 6), (32, 8),
    #             (26, 10), (27, 10), (28, 10),
    #             (21, 13), (22, 13), (23, 13), (24, 13), (25, 13),
    #             (29, 13), (30, 13), (31, 13), (32, 13),
    #             (25, 14), (25, 15), (25, 16), (25, 17), (25, 18), (25, 19),
    #             (23, 17), (24, 17),
    #             (26, 19), (27, 19), (28, 19), (29, 19),
    #             (29, 14), (29, 15), (29, 16), (29, 17), (29, 18),
    #             (22, 20), (22, 21), (22, 22), (22, 23),
    #             (21, 25), (22, 25),
    #             (21, 26), (22, 26),
    #             (19, 27), (20, 27), (21, 27), (22, 27),
    #             (18, 28), (19, 28), (20, 28), (21, 28), (22, 28),
    #             (26, 25), (27, 25), (28, 25), (29, 25), (30, 25), (31, 25),
    #             (31, 26), (32, 26), (33, 26),
    #             (33, 27), (34, 27), (35, 27),
    #             (26, 28), (27, 28), (28, 28), (29, 28),
    #             (35, 6), (36, 6), (37, 6),
    #             (34, 15), (35, 15), (36, 15), (37, 15),
    #             (39, 4), (40, 4),
    #             (39, 10), (40, 10), (41, 10), (42, 10),
    #             (39, 11), (39, 12), (39, 13), (39, 14),
    #             (40, 14), (40, 15), (40, 16), (40, 17),
    #             (38, 17), (39, 17),
    #             (38, 28), (39, 28),
    #             (40, 26), (41, 24), (42, 24),
    #             (43, 1), (43, 2), (43, 3), (43, 4), (43, 5), (43, 6), (43, 7), (43, 8),
    #             (43, 9), (43, 10), (43, 11), (43, 12), (43, 13), (43, 14), (43, 15), (43, 16),
    #             (44, 7), (45, 7),
    #             (44, 14), (45, 14), (46, 14),
    #             (43, 19), (44, 19), (45, 20),
    #             (44, 23), (44, 24), (44, 25), (44, 26), (44, 27), (44, 28),
    #             (45, 22), (46, 22),
    #             (48, 8),
    #             (45, 10), (46, 10),
    #             (48, 12), (48, 16),
    #             (46, 17), (47, 17), (48, 17),
    #             (18, 19), (18, 20),
    #             (2, 10), (3, 10), (4, 10),
    #             (6, 12), (7, 12),
    #             (3, 14), (4, 14),
    #             (8, 15), (9, 15),
    #             (23, 11), (24, 11),
    #             (35, 12), (36, 12), (38, 10),
    #             (35, 20), (36, 20), (37, 20),
    #             (37, 21), (37, 22), (38, 22), (39, 22),
    #             (41, 21), (42, 20),
    #             (31, 18), (32, 19),
    #             (31, 22), (32, 22), (33, 22),
    #             (1, 23), (2, 23)
    #         ]
    #
    #         platform_coords = [(x * TILE, y * TILE) for x, y in platform_coords]
    #
    #     return platform_coords
    #
    # def platform(self):
    #     platform_list = pygame.sprite.Group()
    #     platform_coords = self.get_border_coords() + self.get_platform_coords()
    #     for (x, y) in platform_coords:
    #         platform = tile.Tile(x, y, 'tile.png')
    #         platform_list.add(platform)
    #     return platform_list
    #
    # def goal(self):
    #     goal_list = pygame.sprite.Group()
    #     goal_coords = self.get_goal_coords()
    #     for (x, y) in goal_coords:
    #         goal = tile.Tile(x, y, 'pizza.png', PIZZA_ALPHA)
    #         goal_list.add(goal)
    #     return goal_list


