"""'
Level Object
"""

TILE_DIM = 40
TILE_CHARS = ['#', '?', 'B', 'T']
GOAL_CHAR = '!'
START_CHAR = 'S'
BLANK_CHAR = '-'

MAX_WIDTH = 1200
MAX_HEIGHT = 600


class Level:

    def __init__(self, name, width, height, platform_coords, goal_coords, start_coord):
        self.name = name
        self.width = width  # in px
        self.height = height  # in px
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
        return Level.all_possible_coords(self.width, self.height)

    @staticmethod
    def get_level_dimensions_in_tiles(game, level):
        level_obj = Level.generate_level_from_file(game, level)
        level_w = int(level_obj.get_width() / TILE_DIM)
        level_h = int(level_obj.get_height() / TILE_DIM)
        return level_w, level_h

    @staticmethod
    def all_possible_coords(level_w, level_h):  # level_w and level_h in px
        coords = []
        for x in range(int(level_w / TILE_DIM)):
            for y in range(int(level_h / TILE_DIM)):
                coords.append((x * TILE_DIM, y * TILE_DIM))
        return coords

    @staticmethod
    def generate_level_from_file(game, level):

        add_border_tiles = game != "generated"  # generated levels from solver already include border tiles
        filepath = "level_structural_layers/%s/%s.txt" % (game, level)

        level_width = 0
        level_height = 0
        platform_coords = []
        goal_coords = []
        start_coord = None

        f = open(filepath, 'r')

        for cur_line in f:

            line = cur_line.rstrip()

            # Setup
            if level_width == 0:  # level_width not specified yet
                if add_border_tiles:
                    level_width = len(line) + 2  # add 2 for left and right border tiles in ceiling row
                    platform_coords += [(x * TILE_DIM, level_height * TILE_DIM) for x in range(level_width)]  # add ceiling tiles
                    level_height += 1  # add 1 for ceiling tile row
                else:
                    level_width = len(line)

            # Parse line
            for char_index in range(level_width):

                char_coord = (char_index * TILE_DIM, level_height * TILE_DIM)

                if add_border_tiles and (char_index == 0 or char_index == level_width-1):  # add left and right border tiles
                    platform_coords.append(char_coord)
                else:
                    cur_idx = char_index-1 if add_border_tiles else char_index
                    char = line[cur_idx]
                    if char in TILE_CHARS:
                        platform_coords.append(char_coord)
                    elif char == GOAL_CHAR:
                        goal_coords.append(char_coord)
                    elif start_coord is None and char == START_CHAR:  # start coord can only be defined once
                        start_coord = char_coord

            level_height += 1

        f.close()

        if add_border_tiles:
            platform_coords += [(x * TILE_DIM, level_height * TILE_DIM) for x in range(level_width)]  # add floor tiles
            level_height += 1  # add 1 for floor tile row

        return Level(filepath, level_width * TILE_DIM, level_height * TILE_DIM,
                     platform_coords, goal_coords, start_coord)

