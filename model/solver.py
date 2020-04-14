"""'
Solver Object
"""

import re

from model.level import TILE_DIM, TILE_CHARS, START_CHAR, GOAL_CHAR, BLANK_CHAR


class Solver:

    def __init__(self, prolog_file, level_w, level_h, min_perc_blocks, start_bottom_left, max_sol, save):
        match = re.match('level_saved_files_([^/]+)/prolog_files/([a-zA-Z0-9_-]+).pl', prolog_file)
        player_img, prolog_filename = match.group(1), match.group(2)
        self.prolog_file = prolog_file
        self.prolog_filename = prolog_filename
        self.player_img = player_img

        self.level_w = level_w
        self.level_h = level_h
        self.min_perc_blocks = min_perc_blocks
        self.start_bottom_left = start_bottom_left
        self.max_sol = max_sol
        self.save = save

        self.answer_set_count = 0
        self.set_tile_ids = False
        self.start_tile_id = None
        self.block_tile_id = None
        self.goal_tile_id = None

    def init_tile_ids(self, start_tile_id, block_tile_id, goal_tile_id):
        self.start_tile_id = start_tile_id
        self.block_tile_id = block_tile_id
        self.goal_tile_id = goal_tile_id
        self.set_tile_ids = True

    def increment_answer_set_count(self):
        self.answer_set_count += 1

    def has_next_answer_set(self):
        return self.answer_set_count < self.max_sol

    def get_cur_answer_set_filename(self):
        return "%s_w%d_h%d_a%d" % (self.prolog_filename, self.level_w, self.level_h, self.answer_set_count)

    @staticmethod
    def get_assignments_dict(model_str):
        assignments = re.findall(r'assignment\([0-9t,]*\)', model_str)
        assignments_dict = {}  # {(tile_x, tile_y): tile_id}
        for assignment in assignments:
            match = re.match(r'assignment\((\d+),(\d+),(t\d+)\)', assignment)
            tile_x = int(match.group(1))
            tile_y = int(match.group(2))
            tile_id = match.group(3)
            assignments_dict[(tile_x, tile_y)] = tile_id
        return assignments_dict  # {(tile_x, tile_y): tile_id}

    @staticmethod
    def get_tile_id_coords_map(assignments_dict):
        tile_id_coords_map = {}
        for tile_coord, tile_id in assignments_dict.items():  # {(tile_x, tile_y): tile_id}
            if tile_id_coords_map.get(tile_id) is None:
                tile_id_coords_map[tile_id] = []
            metatile_coord = (tile_coord[0] * TILE_DIM, tile_coord[1] * TILE_DIM)
            tile_id_coords_map[tile_id].append(metatile_coord)

        tile_id_coords_map_with_extra_info = {}
        for tile_id, coords in tile_id_coords_map.items():
            extra_info = "S" if len(coords) == 1 else ""
            tile_id_coords_map_with_extra_info[(tile_id, extra_info)] = coords

        return tile_id_coords_map_with_extra_info

    def generate_level_structural_txt(self, assignments_dict):
        if not self.set_tile_ids:
            print("Error: Initialize tile ids in Solver object before calling generate_level_structural_txt().")
            exit(0)

        def get_tile_char(tile_id):
            if tile_id == self.block_tile_id:
                return TILE_CHARS[0]
            elif tile_id == self.start_tile_id:
                return START_CHAR
            elif tile_id == self.goal_tile_id:
                return GOAL_CHAR
            else:
                return BLANK_CHAR

        level_structural_txt = ""
        for row in range(self.level_h):
            for col in range(self.level_w):
                tile_xy = (col, row)
                tile_id = assignments_dict.get(tile_xy)
                tile_char = get_tile_char(tile_id)
                level_structural_txt += tile_char
            level_structural_txt += "\n"
        return level_structural_txt

    def get_tmp_prolog_statements(self):
        if not self.set_tile_ids:
            print("Error: Initialize tile ids in Solver object before calling get_tmp_prolog_statements().")
            exit(0)

        tmp_prolog_statements = ""
        tmp_prolog_statements += "dim_width(0..%d).\n" % (self.level_w - 1)
        tmp_prolog_statements += "dim_height(0..%d).\n" % (self.level_h - 1)

        # Create tile facts
        create_tiles_statement = "tile(TX,TY) :- dim_width(TX), dim_height(TY)."
        tmp_prolog_statements += create_tiles_statement + "\n"

        # Set border tiles to be block tiles
        block_tile_coords = []
        for x in range(self.level_w):
            block_tile_coords += [(x, 0), (x, self.level_h - 1)]
        for y in range(self.level_h):
            block_tile_coords += [(0, y), (self.level_w - 1, y)]
        for x, y in list(set(block_tile_coords)):
            block_tile_assignment = "assignment(%d, %d, %s)." % (x, y, self.block_tile_id)
            tmp_prolog_statements += block_tile_assignment + "\n"

        # Fix start tile to bottom left of the generated level
        if self.start_bottom_left:
            start_tile_assignment = "assignment(%d, %d, %s)." % (1, self.level_h - 2, self.start_tile_id)
            tmp_prolog_statements += start_tile_assignment + "\n"

        # Set minimum percentage of block tiles allowed in generated level
        if self.min_perc_blocks is not None:
            # Limit number of block tiles
            total_tiles = int(self.level_w * self.level_h)
            min_perc_blocks_statement = "limit(%s, %d, %d)." % (
                self.block_tile_id, int(self.min_perc_blocks / 100 * total_tiles), total_tiles)
            tmp_prolog_statements += min_perc_blocks_statement + "\n"

        return tmp_prolog_statements
