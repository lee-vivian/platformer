"""'
Level Object
"""

TILE_DIM = 40

TILE_CHARS = {
    'block': {
        'X': ['solid', 'ground'],
        'S': ['solid', 'breakable'],
        '<': ['solid', 'top-left pipe', 'pipe'],
        '>': ['solid', 'top-right pipe', 'pipe'],
        '[': ['solid', 'left pipe', 'pipe'],
        ']': ['solid', 'right pipe', 'pipe'],
        'B': ['cannon top', 'cannon', 'solid', 'hazard'],
        'b': ['cannon bottom', 'cannon', 'solid'],
        '#': ['solid', 'ground']
    },
    'bonus': {
        '?': ["solid","question block", "full question block"],
        'Q': ["solid","question block", "empty question block"]
    },
    'start': {
        '*': ['start']
    },
    'goal': {
        '!': ['goal']
    },
    'empty': {
        '-': ['passable', 'empty'],
        'E': ['enemy', 'damaging', 'hazard', 'moving'],
        'o': ['coin', 'collectable', 'passable']
    }
}


MAX_WIDTH = 1200
MAX_HEIGHT = 600


class Level:

    def __init__(self, name, game, width, height, platform_coords, goal_coords, start_coord, bonus_coords):
        self.name = name
        self.game = game
        self.width = width  # in px
        self.height = height  # in px
        self.platform_coords = platform_coords
        self.goal_coords = goal_coords
        self.start_coord = start_coord
        self.bonus_coords = bonus_coords

    def get_name(self):
        return self.name

    def get_game(self):
        return self.game

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

    def get_bonus_coords(self):
        return list(self.bonus_coords)

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
    def print_start_goal_tile_locations(game, level):
        level_obj = Level.generate_level_from_file(game, level)
        start_x, start_y = level_obj.get_start_coord()
        start_tile_x, start_tile_y = int(start_x / TILE_DIM), int(start_y / TILE_DIM)
        print("Start Tile: %s" % str((start_tile_x, start_tile_y)))

        goal_tile_coords = []
        for goal_x, goal_y in level_obj.get_goal_coords():
            goal_tile_x, goal_tile_y = int(goal_x / TILE_DIM), int(goal_y / TILE_DIM)
            goal_tile_coords.append((goal_tile_x, goal_tile_y))
        print("Goal Tile: %s" % str(goal_tile_coords))

    @staticmethod
    def print_tile_summary(game, level):
        filepath = "level_structural_layers/%s/%s.txt" % (game, level)
        num_tiles, num_start_tiles, num_goal_tiles, num_bonus_tiles, num_block_tiles = 0, 0, 0, 0, 0
        f = open(filepath, 'r')
        for line in f:
            for char in line.rstrip():  # for each char in the line
                if TILE_CHARS['start'].get(char) is not None:
                    num_start_tiles += 1
                elif TILE_CHARS['goal'].get(char) is not None:
                    num_goal_tiles += 1
                elif TILE_CHARS['bonus'].get(char) is not None:
                    num_bonus_tiles += 1
                elif TILE_CHARS['block'].get(char) is not None:
                    num_block_tiles += 1
                num_tiles += 1
        f.close()

        print("Level: %s/%s" % (game, level))
        print("Total tiles: %d (%d%%)" % (num_tiles, num_tiles / num_tiles * 100))
        print("Block tiles:  %d (%d%%)" % (num_block_tiles, num_block_tiles / num_tiles * 100))
        print("Bonus tiles: %d (%d%%)" % (num_bonus_tiles, num_bonus_tiles / num_tiles * 100))
        # print("Start tiles:  %d (%d%%)" % (num_start_tiles, num_start_tiles / num_tiles * 100))
        # print("Goal tiles:  %d (%d%%)" % (num_goal_tiles, num_goal_tiles / num_tiles * 100))

    @staticmethod
    def print_structural_txt(game, level):
        filepath = "level_structural_layers/%s/%s.txt" % (game, level)
        f = open(filepath, 'r')
        structural_txt = f.read()
        print(structural_txt)

    @staticmethod
    def generate_level_from_file(game, level):
        filepath = "level_structural_layers/%s/%s.txt" % (game, level)
        level_width, level_height = 0, 0
        platform_coords = []
        bonus_coords = []
        goal_coords = []
        start_coord = None

        f = open(filepath, 'r')

        for cur_line in f:

            line = cur_line.rstrip()

            # Set the level_width
            level_width = len(line) if level_width == 0 else level_width

            # Parse each char in the line
            for char_index in range(level_width):
                char_coord = (char_index * TILE_DIM, level_height * TILE_DIM)
                char = line[char_index]

                if TILE_CHARS['block'].get(char) is not None:
                    platform_coords.append(char_coord)
                elif TILE_CHARS['bonus'].get(char) is not None:
                    bonus_coords.append(char_coord)
                elif start_coord is None and TILE_CHARS['start'].get(char) is not None:   # define start coord once
                    start_coord = char_coord
                elif TILE_CHARS['goal'].get(char) is not None:
                    goal_coords.append(char_coord)

            # Increment the level_height
            level_height += 1

        f.close()

        return Level(name=level, game=game, width=level_width * TILE_DIM, height=level_height * TILE_DIM,  # in px
                     platform_coords=platform_coords, goal_coords=goal_coords, start_coord=start_coord,
                     bonus_coords=bonus_coords)
