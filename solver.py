"""'
Solver Object
"""

import clingo
import re
import networkx as nx

from model.metatile import Metatile
from model.level import TILE_DIM, TILE_CHARS, START_CHAR, GOAL_CHAR, BLANK_CHAR
from stopwatch import Stopwatch
from utils import get_directory, get_filepath, write_pickle, read_pickle, write_file, error_exit, get_node_at_coord


class Solver:

    def __init__(self, prolog_file, level_w, level_h, min_perc_blocks, start_bottom_left, print_level_stats, save,
                 validate, start_tile_id, block_tile_id, goal_tile_id):
        self.prolog_file = prolog_file
        self.level_w = level_w
        self.level_h = level_h
        self.min_perc_blocks = min_perc_blocks
        self.start_bottom_left = start_bottom_left
        self.print_level_stats = print_level_stats
        self.save = save
        self.validate = validate

        self.tile_ids = {"start": start_tile_id, "block": block_tile_id, "goal": goal_tile_id}
        self.tmp_prolog_statements = ""
        self.init_tmp_prolog_statements()  # create tmp prolog statements
        self.answer_set_count = 0

        # { answer_set_filename: { tile_id_coord_map: map, start_coord: coord, goal_coord: coord} }
        self.generated_levels_dict = {}
        self.stopwatch = Stopwatch()

    @staticmethod
    def parse_prolog_filepath(prolog_filepath):
        match = re.match('level_saved_files_([^/]+)/prolog_files/([a-zA-Z0-9_-]+).pl', prolog_filepath)
        player_img = match.group(1)
        prolog_filename = match.group(2)
        return player_img, prolog_filename

    def get_command_str(self):
        player_img, prolog_filename = Solver.parse_prolog_filepath(self.prolog_file)
        return "prolog: %s, width: %d, height: %d, min_perc_blocks: %s, start_bottom_left: %s" % \
               (prolog_filename, self.level_w, self.level_h, str(self.min_perc_blocks), str(self.start_bottom_left))

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
        prg.configuration.solve.models = max_sol  # compute at most max_sol models (0 = all)

        self.stopwatch.start()  # start the stopwatch

        print("----- LOADING -----")
        print("Loading prolog file: %s..." % self.prolog_file)
        prg.load(self.prolog_file)
        print(self.stopwatch.get_lap_time_str("Load prolog file"))

        print("Adding %d tmp_prolog_statements..." % (len(self.tmp_prolog_statements.split("\n"))))
        with prg.builder() as builder:
            clingo.parse_program(self.tmp_prolog_statements, lambda stm: builder.add(stm))
        print(self.stopwatch.get_lap_time_str("Parse tmp prolog statements"))

        prg.add('base', [], "")

        print("Grounding...")
        prg.ground([('base', [])])
        print(self.stopwatch.get_lap_time_str("Ground"))

        print("----- SOLVING -----")
        prg.solve(on_model=lambda m: self.process_answer_set(repr(m)))
        print(self.stopwatch.get_lap_time_str("Solve"))

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

    def create_tile_id_coords_map(self, assignments_dict, player_img, answer_set_filename):

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

    def get_fact_coord(self, model_str, fact_name):
        facts = re.findall(r'%s\([0-9t,]*\)' % fact_name, model_str)
        if len(facts) == 0:
            error_exit("Fact '%s' not found in solver output" % fact_name)
        fact = facts[0]
        match = re.match(r'%s\((\d+),(\d+)\)' % fact_name, fact)
        x, y = int(match.group(1)), int(match.group(2))
        return x, y

    def add_to_generated_levels_dict(self, answer_set_filename, tile_id_coords_map, start_coord, goal_coord):
        self.generated_levels_dict[answer_set_filename] = {
            'tile_id_coords_map': tile_id_coords_map,
            'start_coord': start_coord,
            'goal_coord': goal_coord
        }

    def process_answer_set(self, model_str):
        player_img, prolog_filename = Solver.parse_prolog_filepath(self.prolog_file)
        answer_set_filename = self.get_cur_answer_set_filename(prolog_filename)

        # Create assignments dictionary {(tile_x, tile_y): tile_id}
        assignments_dict = self.create_assignments_dict(model_str)

        # Create {(tile_id, extra_info): coords} map
        tile_id_extra_info_coords_map = self.create_tile_id_coords_map(assignments_dict, player_img, answer_set_filename)

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
            print("Total tiles: %d (%d%%)" % (num_tiles, num_tiles / num_tiles * 100))
            print("Block tiles:  %d (%d%%)" % (num_block_tiles, num_block_tiles / num_tiles * 100))
            print("Start tiles:  %d (%d%%)" % (num_start_tiles, num_start_tiles / num_tiles * 100))
            print("Goal tiles:  %d (%d%%)" % (num_goal_tiles, num_goal_tiles / num_tiles * 100))

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
            level_structural_txt_file = get_filepath(generated_level_txt_dir, "%s.txt" % answer_set_filename)
            write_file(level_structural_txt_file, level_structural_txt)

        print(level_structural_txt)  # TODO uncomment

        # Add to generated_levels_dict if validate is True
        if self.validate:
            self.add_to_generated_levels_dict(answer_set_filename=answer_set_filename,
                                              tile_id_coords_map=tile_id_extra_info_coords_map,
                                              start_coord=self.get_fact_coord(model_str, 'start'),
                                              goal_coord=self.get_fact_coord(model_str, 'goal'))

        # Increment answer set count
        self.increment_answer_set_count()

    def end_and_validate(self):
        self.stopwatch.stop()  # stop stopwatch

        if not self.validate:
            print("----- SUMMARY -----")
            print("Levels generated: %d" % self.answer_set_count)

        # Validate generated levels
        else:
            self.stopwatch.start()  # start stopwatch
            print("----- VALIDATING -----")
            player_img, prolog_filename = Solver.parse_prolog_filepath(self.prolog_file)
            level_saved_files_dir = "level_saved_files_%s/" % player_img
            generated_state_graph_dir = get_directory(level_saved_files_dir + "generated_state_graphs")
            invalid_level_count = 0
            valid_level_count = 0

            # Load id_metatile_map
            id_metatile_map_file = get_filepath(level_saved_files_dir + "id_metatile_maps", "%s.pickle" % prolog_filename)
            id_metatile_map = read_pickle(id_metatile_map_file)

            for answer_set_filename, answer_set_dict in self.generated_levels_dict.items():
                print("Validating generated level: %s..." % answer_set_filename)
                tile_id_extra_info_coords_map = answer_set_dict.get('tile_id_coords_map')
                start_coord = answer_set_dict.get('start_coord')
                goal_coord = answer_set_dict.get('goal_coord')

                # Create state graph for generated level
                state_graph = nx.DiGraph()
                for (tile_id, extra_info), coords in tile_id_extra_info_coords_map.items():
                    metatile_dict = eval(id_metatile_map.get(tile_id))
                    metatile_state_graph = nx.DiGraph(metatile_dict.get('graph'))
                    if nx.is_empty(metatile_state_graph):
                        continue
                    for coord in coords:
                        unnormalized_metatile_state_graph = Metatile.get_normalized_graph(metatile_state_graph, coord, normalize=False)
                        state_graph = nx.compose(state_graph, unnormalized_metatile_state_graph)

                # Get src_node and dest_node
                src_node = get_node_at_coord(state_graph, start_coord)
                dest_node = get_node_at_coord(state_graph, goal_coord)

                # Check if valid path exists from start to goal
                if src_node is None or dest_node is None or not nx.has_path(state_graph, src_node, dest_node):
                    print("Invalid level: %s" % answer_set_filename)
                    invalid_level_count += 1
                else:
                    state_graph_file = get_filepath(generated_state_graph_dir, "%s.gpickle" % answer_set_filename)
                    nx.write_gpickle(state_graph, state_graph_file)
                    print("Saved to: %s" % state_graph_file)
                    valid_level_count += 1

            print(self.stopwatch.get_lap_time_str("Validation"))
            self.stopwatch.stop()

            print("----- SUMMARY -----")
            print("Command: [%s]" % self.get_command_str())
            print("Levels generated: %d" % self.answer_set_count)
            print("Valid levels : %d" % valid_level_count)
            print("Invalid levels: %d" % invalid_level_count)

        return True

