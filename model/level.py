"""'
Level Object
"""

from utils import error_exit, write_file

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
    },
    'one_way_platform': {
        'T': ['solidtop', 'passable', 'platform'],
        'M': ['solidtop', 'passable', 'moving', 'platform']
    },
    'door': {
        'D': ['solid', 'openable', 'door']
    },
    'hazard': {
        'H': ['solid', 'damaging', 'hazard']
    },
    'wall': {
        'W': ['solid', 'border', 'wall']
    },
    'permeable_wall': {
        '|': ['permeable', 'border', 'wall']
    }
}


MAX_WIDTH = 1200
MAX_HEIGHT = 600


class Level:

    def __init__(self, name, game, width, height, platform_coords, goal_coords, start_coord, bonus_coords,
                 one_way_platform_coords, hazard_coords, wall_coords, permeable_wall_coords):
        self.name = name
        self.game = game
        self.width = width  # in px
        self.height = height  # in px
        self.platform_coords = platform_coords
        self.goal_coords = goal_coords
        self.start_coord = start_coord
        self.bonus_coords = bonus_coords
        self.one_way_platform_coords = one_way_platform_coords
        self.hazard_coords = hazard_coords
        self.wall_coords = wall_coords
        self.permeable_wall_coords = permeable_wall_coords

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

    def get_one_way_platform_coords(self):
        return list(self.one_way_platform_coords)

    def get_hazard_coords(self):
        return list(self.hazard_coords)

    def get_wall_coords(self):
        return list(self.wall_coords)

    def get_permeable_wall_coords(self):
        return list(self.permeable_wall_coords)

    def get_all_possible_coords(self):
        return Level.all_possible_coords(self.width, self.height)

    @staticmethod
    def get_level_dimensions_in_tiles(game, level):
        level_obj = Level.generate_level_from_file(game, level)
        level_w = int(level_obj.get_width() / TILE_DIM)
        level_h = int(level_obj.get_height() / TILE_DIM)
        return level_w, level_h

    @staticmethod
    def get_perc_tiles_map(game, level):
        level_obj = Level.generate_level_from_file(game, level)
        total_tiles = len(level_obj.get_all_possible_coords())
        num_tiles_map = {
            'block': len(level_obj.get_platform_coords()),
            'bonus': len(level_obj.get_bonus_coords()),
            'one_way_platform': len(level_obj.get_one_way_platform_coords()),
            'hazard': len(level_obj.get_hazard_coords()),
            'wall': len(level_obj.get_wall_coords()),
            'permeable_wall': len(level_obj.get_permeable_wall_coords())
        }
        perc_tiles_map = {}
        for tile_type, count in num_tiles_map.items():
            perc_tiles_map[tile_type] = int(count / total_tiles * 100)

        return perc_tiles_map

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

        goal_tile_coords = []
        for goal_x, goal_y in level_obj.get_goal_coords():
            goal_tile_x, goal_tile_y = int(goal_x / TILE_DIM), int(goal_y / TILE_DIM)
            goal_tile_coords.append((goal_tile_x, goal_tile_y))

        print("Tile coords:")
        print("  - start: %s" % str((start_tile_x, start_tile_y)))
        print("  - goals: %s" % str(goal_tile_coords))

    @staticmethod
    def get_num_gaps(game, level):
        filepath = "level_structural_layers/%s/%s.txt" % (game, level)
        num_gaps = 0
        floor_line = None

        lines = []
        f = open(filepath, 'r')
        for line in f:
            lines.append(line.rstrip())

        for line in reversed(lines):
            char_is_wall = [TILE_CHARS['wall'].get(char) is not None for char in line]
            all_wall_chars = all(char_is_wall)
            if not all_wall_chars:
                floor_line = line  # first line (starting from the bottom) that is not all wall tiles
                break

        if floor_line is None:
            error_exit("No floor line in file. Every line is composed of wall tiles only.")

        for char in floor_line:
            if TILE_CHARS['hazard'].get(char) is not None:
                num_gaps += 1

        return num_gaps

    @staticmethod
    def print_tile_summary(game, level):
        level_obj = Level.generate_level_from_file(game, level)
        num_tiles_total = len(level_obj.get_all_possible_coords())
        num_tiles_dict = {
            'start': 1,
            'goal': len(level_obj.get_goal_coords()),
            'block': len(level_obj.get_platform_coords()),
            'bonus': len(level_obj.get_bonus_coords()),
            'one_way_platform': len(level_obj.get_one_way_platform_coords()),
            'hazard': len(level_obj.get_hazard_coords()),
            'wall': len(level_obj.get_wall_coords()),
            'permeable_wall': len(level_obj.get_permeable_wall_coords())
        }

        num_tiles_dict['empty'] = num_tiles_total - sum(num_tiles_dict.values())

        print("----- Level: %s/%s -----" % (game, level))
        print("Total tiles: %d (%d%%)" % (num_tiles_total, 100))
        for tile_type, count in num_tiles_dict.items():
            print("  - %s tiles: %d (%d%%)" % (tile_type, count, count / num_tiles_total * 100))

    @staticmethod
    def print_structural_txt(game, level):
        filepath = "level_structural_layers/%s/%s.txt" % (game, level)
        f = open(filepath, 'r')
        structural_txt = f.read()
        print(structural_txt)

    @staticmethod
    def get_uniform_tile_chars(game, level):
        filepath = "level_structural_layers/%s/%s.txt" % (game, level)
        f = open(filepath, 'r')

        uniform_chars = ""
        for line in f:
            line = line.rstrip()
            for char in line:
                for tile_type in TILE_CHARS.keys():
                    tile_type_dict = TILE_CHARS.get(tile_type)
                    match = tile_type_dict.get(char) is not None
                    if match:
                        uniform_char = list(tile_type_dict.keys())[0]  # use first char in tile type dictionary
                        uniform_chars += uniform_char
            uniform_chars += "\n"
        write_file(filepath, uniform_chars)

    @staticmethod
    def generate_level_from_file(game, level):
        filepath = "level_structural_layers/%s/%s.txt" % (game, level)
        level_w, level_h = 0, 0
        prev_line_dict = {}
        tile_coords_dict = {}
        for tile_type in TILE_CHARS.keys():
            tile_coords_dict[tile_type] = []

        f = open(filepath, 'r')

        # Read in each line in file
        for cur_line in f:
            line = cur_line.rstrip()
            level_w = len(line) if level_w == 0 else level_w

            # Parse chars in each line
            for char_idx in range(level_w):
                char = line[char_idx]
                char_coord = (char_idx * TILE_DIM, level_h * TILE_DIM)

                # Test each tile type for a char match
                for tile_type in TILE_CHARS.keys():
                    match = TILE_CHARS[tile_type].get(char) is not None
                    if not match:
                        pass
                    elif tile_type == 'door':
                        char_above = prev_line_dict.get(char_idx)
                        char_above_is_door = TILE_CHARS['door'].get(char_above) is not None
                        if not char_above_is_door:
                            tile_coords_dict['bonus'].append(char_coord)  # read as bonus char if char above != door
                    else:
                        tile_coords_dict[tile_type].append(char_coord)

                # Update prev_line_dict
                prev_line_dict[char_idx] = char

            # Increment level_h
            level_h += 1

        f.close()

        return Level(name=level, game=game, width=level_w * TILE_DIM, height=level_h * TILE_DIM,  # in px
                     platform_coords=tile_coords_dict['block'], goal_coords=tile_coords_dict['goal'],
                     start_coord=tile_coords_dict['start'][0],
                     bonus_coords=tile_coords_dict['bonus'],
                     one_way_platform_coords=tile_coords_dict['one_way_platform'],
                     hazard_coords=tile_coords_dict['hazard'],
                     wall_coords=tile_coords_dict['wall'],
                     permeable_wall_coords=tile_coords_dict['permeable_wall'])
