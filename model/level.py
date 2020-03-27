"""'
Level Object
"""

TILE_DIM = 40
TILE_CHARS = ['#', '?', 'B', 'T']
GOAL_CHAR = '!'
START_CHAR = 'S'

MAX_WIDTH = 1200
MAX_HEIGHT = 600

LEVEL_STRUCTURES_DIR = "level_structural_layers/"


class Level:

    def __init__(self, name, width, height, platform_coords, goal_coords, start_coord):
        self.name = name
        self.width = width
        self.height = height
        self.platform_coords = platform_coords
        self.goal_coords = goal_coords
        self.start_coord = start_coord

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_platform_coords(self):
        return list(self.platform_coords)

    def get_goal_coords(self):
        return list(self.goal_coords)

    def get_start_coord(self):
        return self.start_coord

    def get_all_possible_coords(self):
        coords = []
        for x in range(int(self.width / TILE_DIM)):
            for y in range(int(self.height / TILE_DIM)):
                coords.append((x * TILE_DIM, y * TILE_DIM))
        return coords

    @staticmethod
    def get_level_dimensions(game, level):
        level_obj = Level.generate_level_from_file(game, level)
        level_w = int(level_obj.get_width() / TILE_DIM)
        level_h = int(level_obj.get_height() / TILE_DIM)
        return level_w, level_h

    @staticmethod
    def generate_level_from_file(game, level):
        filepath = "%s/%s.txt" % (game, level)
        level_width = 0
        level_height = 0
        platform_coords = []
        goal_coords = []
        start_coord = None

        f = open(LEVEL_STRUCTURES_DIR + filepath, 'r')

        for cur_line in f:

            line = cur_line.rstrip()

            # Setup
            if level_width == 0:
                level_width = len(line) + 2  # get level width + 2 for left and right border tiles
                for x in range(level_width):
                    platform_coords.append((x * TILE_DIM, level_height * TILE_DIM))  # add ceiling tiles
                level_height += 1

            # Parse line
            for char_index in range(level_width):

                char_coord = (char_index * TILE_DIM, level_height * TILE_DIM)

                if char_index == 0 or char_index == level_width-1:  # add left and right border tiles
                    platform_coords.append(char_coord)
                else:
                    char = line[char_index - 1]
                    if char in TILE_CHARS:
                        platform_coords.append(char_coord)
                    elif char == GOAL_CHAR:
                        goal_coords.append(char_coord)
                    elif start_coord is None and char == START_CHAR:
                        start_coord = char_coord

            level_height += 1

        f.close()

        # add floor tiles
        for x in range(level_width):
            platform_coords.append((x * TILE_DIM, level_height * TILE_DIM))
        level_height += 1

        return Level(filepath, level_width * TILE_DIM, level_height * TILE_DIM,
                     platform_coords, goal_coords, start_coord)

