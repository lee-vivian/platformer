"""'
Solver Object
"""

import clingo
import re

from model.level import TILE_DIM, TILE_CHARS, START_CHAR, GOAL_CHAR, BLANK_CHAR
from utils import get_filepath, write_pickle, write_file


class Solver:

    def __init__(self, prolog_file, level_w, level_h, min_perc_blocks, start_bottom_left, print_level_stats, save,
                 start_tile_id, block_tile_id, goal_tile_id):
        self.prolog_file = prolog_file
        self.level_w = level_w
        self.level_h = level_h
        self.min_perc_blocks = min_perc_blocks
        self.start_bottom_left = start_bottom_left
        self.print_level_stats = print_level_stats
        self.save = save

        self.tile_ids = {"start": start_tile_id, "block": block_tile_id, "goal": goal_tile_id}
        self.tmp_prolog_statements = ""
        self.init_tmp_prolog_statements()  # create tmp prolog statements
        self.answer_set_count = 0

    @staticmethod
    def parse_prolog_filepath(prolog_filepath):
        match = re.match('level_saved_files_([^/]+)/prolog_files/([a-zA-Z0-9_-]+).pl', prolog_filepath)
        player_img = match.group(1)
        prolog_filename = match.group(2)
        return player_img, prolog_filename

    def increment_answer_set_count(self):
        self.answer_set_count += 1

    def get_cur_answer_set_filename(self, prolog_filename):
        return "%s_w%d_h%d_a%d" % (prolog_filename, self.level_w, self.level_h, self.answer_set_count)

    def init_tmp_prolog_statements(self):
        start_tile_id = self.tile_ids.get('start')
        block_tile_id = self.tile_ids.get('block')

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
            block_tile_assignment = "assignment(%d, %d, %s)." % (x, y, block_tile_id)
            tmp_prolog_statements += block_tile_assignment + "\n"

        # Fix start tile to bottom left of the generated level
        if self.start_bottom_left:
            start_tile_assignment = "assignment(%d, %d, %s)." % (1, self.level_h - 2, start_tile_id)
            tmp_prolog_statements += start_tile_assignment + "\n"

        # Set minimum percentage of block tiles allowed in generated level
        if self.min_perc_blocks is not None:
            # Limit number of block tiles
            total_tiles = int(self.level_w * self.level_h)
            min_perc_blocks_statement = "limit(%s, %d, %d)." % (
                block_tile_id, int(self.min_perc_blocks / 100 * total_tiles), total_tiles)
            tmp_prolog_statements += min_perc_blocks_statement + "\n"

        # Set tmp_prolog_statements
        self.tmp_prolog_statements = tmp_prolog_statements
        return True

    def solve(self, max_sol):
        prg = clingo.Control([])
        prg.configuration.solve.__desc_models
        prg.configuration.solve.models = max_sol  # compute at most max_sol models (0 = all)
        prg.load(self.prolog_file)  # load statements from prolog file
        with prg.builder() as builder:
            clingo.parse_program(self.tmp_prolog_statements, lambda stm: builder.add(stm))  # add tmp prolog statements
        prg.add('base', [], "")
        prg.ground([('base', [])])
        prg.solve(on_model=lambda m: self.process_answer_set(repr(m)))

    def create_assignments_dict(self, model_str):
        assignments = re.findall(r'assignment\([0-9t,]*\)', model_str)
        assignments_dict = {}  # {(tile_x, tile_y): tile_id}
        for assignment in assignments:
            match = re.match(r'assignment\((\d+),(\d+),(t\d+)\)', assignment)
            tile_x = int(match.group(1))
            tile_y = int(match.group(2))
            tile_id = match.group(3)
            assignments_dict[(tile_x, tile_y)] = tile_id
        return assignments_dict  # {(tile_x, tile_y): tile_id}

    def create_tile_id_coords_map(self, assignments_dict, player_img, prolog_filename):

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

        if self.save:
            tile_id_coords_map_dir = "level_saved_files_%s/tile_id_coords_maps/" % player_img
            answer_set_filename = self.get_cur_answer_set_filename(prolog_filename)
            tile_id_coords_map_file = get_filepath(tile_id_coords_map_dir, "%s.pickle" % answer_set_filename)
            write_pickle(tile_id_coords_map_file, tile_id_coords_map_with_extra_info)

        return tile_id_coords_map_with_extra_info

    def get_tile_char(self, tile_id):
        if tile_id == self.tile_ids.get('block'):
            return TILE_CHARS[0]
        elif tile_id == self.tile_ids.get('start'):
            return START_CHAR
        elif tile_id == self.tile_ids.get('goal'):
            return GOAL_CHAR
        else:
            return BLANK_CHAR

    def process_answer_set(self, model_str):

        player_img, prolog_filename = Solver.parse_prolog_filepath(self.prolog_file)

        # Create assignments dictionary {(tile_x, tile_y): tile_id}
        assignments_dict = self.create_assignments_dict(model_str)

        # Create {(tile_id, extra_info): coords} map
        tile_id_extra_info_coords_map = self.create_tile_id_coords_map(assignments_dict, player_img, prolog_filename)

        # Print tiles per level
        if self.print_level_stats:
            num_tiles, num_start_tiles, num_block_tiles, num_goal_tiles = 0, 0, 0, 0
            for (tile_id, extra_info), coords in tile_id_extra_info_coords_map.items():
                len_coords = len(coords)
                num_tiles += len_coords
                if tile_id == self.tile_ids.get('block'):
                    num_block_tiles += len_coords
                elif tile_id == self.tile_ids.get('start'):
                    num_start_tiles += len_coords
                elif tile_id == self.tile_ids.get('goal'):
                    num_goal_tiles += len_coords
            print("Total tiles: %d (%d/100)" % (num_tiles, num_tiles / num_tiles * 100))
            print("Block tiles:  %d (%d/100)" % (num_block_tiles, num_block_tiles / num_tiles * 100))
            print("Start tiles:  %d (%d/100)" % (num_start_tiles, num_start_tiles / num_tiles * 100))
            print("Goal tiles:  %d (%d/100)" % (num_goal_tiles, num_goal_tiles / num_tiles * 100))

        # Create and save structural txt file for the generated level
        level_structural_txt = ""
        for row in range(self.level_h):
            for col in range(self.level_w):
                tile_xy = (col, row)
                tile_id = assignments_dict.get(tile_xy)
                tile_char = self.get_tile_char(tile_id)
                level_structural_txt += tile_char
            level_structural_txt += "\n"

        if self.save:
            generated_level_txt_dir = "level_structural_layers/generated/"
            answer_set_filename = self.get_cur_answer_set_filename(prolog_filename)
            level_structural_txt_file = get_filepath(generated_level_txt_dir, "%s.txt" % answer_set_filename)
            write_file(level_structural_txt_file, level_structural_txt)

        print(level_structural_txt)

        # TODO VALIDATE(need tile_id_extra_info_coords_map, start_coord, goal_coord of answer set
        #   start_coord = get_fact_coord(model_str, 'start')
        #   goal_coord = get_fact_coord(model_str, 'goal')
        # def get_fact_coord(model_str, fact_name):
        #     facts = re.findall(r'%s\([0-9t,]*\)' % fact_name, model_str)
        #     if len(facts) == 0:
        #         error_exit("Fact '%s' not found in solver output" % fact_name)
        #     fact = facts[0]
        #     match = re.match(r'%s\((\d+),(\d+)\)' % fact_name, fact)
        #     x, y = int(match.group(1)), int(match.group(2))
        #     return x, y

        # Increment answer set count
        self.increment_answer_set_count()

        # >> > import clingo
        # >> > prg = clingo.Control()
        # >> > prg.configuration.solve.__desc_models
        # 'Compute at most %A models (0 for all)\n'
        # >> > prg.configuration.solve.models = 0
        # >> > prg.add("base", [], "{a;b}.")
        # >> > prg.ground([("base", [])])
        # >> > prg.solve(on_model=lambda m: print("Answer: {}".format(m)))
        # Answer:
        # Answer: a
        # Answer: b
        # Answer: a
        # b
        # SAT
