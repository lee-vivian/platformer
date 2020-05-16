"""
Solver Object
"""

import clingo
import re
import networkx as nx
import random
from datetime import datetime

from model.metatile import Metatile
from model.level import TILE_DIM, TILE_CHARS
from stopwatch import Stopwatch
from utils import get_directory, get_filepath, write_pickle, read_pickle, write_file, error_exit, get_node_at_coord, get_unique_lines


class Solver:

    def __init__(self, prolog_file, config, config_filename, tile_ids, print_level_stats, print_level, save, validate):
        self.prolog_file = prolog_file
        self.config_filename = config_filename
        self.level_w = config.get('level_w')
        self.level_h = config.get('level_h')
        self.forced_tiles = config.get('forced_tiles')                  # {type: list-of-tile-coords}
        self.reachable_tiles = config.get('reachable_tiles')            # list-of-tile-coords
        self.num_tile_ranges = config.get('num_tile_ranges')            # { type: {'min': min, 'max': max} }
        self.perc_tile_ranges = config.get('perc_tile_ranges')          # { type: {'min': min, 'max': max} }
        self.tile_position_ranges = config.get('tile_position_ranges')  # { position: {'min': min, 'max': max} }
        self.allow_pits = config.get('allow_pits')                      # bool
        self.tile_ids = tile_ids                                        # { tile_type: list-of-tile-ids }
        self.print_level_stats = print_level_stats
        self.print_level = print_level
        self.save = save
        self.validate = validate

        self.tmp_prolog_statements = ""
        self.init_tmp_prolog_statements()  # create tmp prolog statements
        self.answer_set_count = 0

        # { answer_set_filename: { tile_id_coord_map: map, start_coord: coord, goal_coord: coord} }
        self.generated_levels_dict = {}
        self.stopwatch = Stopwatch()

    @staticmethod
    def parse_prolog_filepath(prolog_filepath):
        match = re.match('level_saved_files_([^/]+)/prolog_files/([a-zA-Z0-9_\-]+)\.pl', prolog_filepath)
        player_img = match.group(1)
        prolog_filename = match.group(2)
        return player_img, prolog_filename

    def increment_answer_set_count(self):
        self.answer_set_count += 1

    def get_cur_answer_set_filename(self, prolog_filename):
        filename_components = [prolog_filename, self.config_filename, "a%d" % self.answer_set_count,
                               "a%d" % self.answer_set_count]
        return "_".join(filename_components)

    def init_tmp_prolog_statements(self):
        tmp_prolog_statements = ""
        tmp_prolog_statements += "dim_width(0..%d).\n" % (self.level_w - 1)
        tmp_prolog_statements += "dim_height(0..%d).\n" % (self.level_h - 1)
        num_total_tiles = int(self.level_w * self.level_h)

        # Create tile facts
        create_tiles_statement = "tile(TX,TY) :- dim_width(TX), dim_height(TY)."
        tmp_prolog_statements += create_tiles_statement + "\n"

        # Get tile ids for different tile types
        start_tile_id = self.tile_ids.get('start')[0]
        block_tile_id = self.tile_ids.get('block')[0]
        goal_tile_id = self.tile_ids.get('goal')[0]
        one_way_tile_ids = self.tile_ids.get('one_way_platform')

        # Create one_way facts for one_way_platform tile assignments
        if len(one_way_tile_ids) > 0:
            tmp_prolog_statements += "one_way_tile(X,Y) :- assignment(X,Y,%s).\n" % ';'.join(one_way_tile_ids)

        # Get non-empty tile ids
        non_empty_tile_ids = []
        for tile_type, tile_ids in self.tile_ids.items():
            non_empty_tile_ids += tile_ids

        # Create non_empty_tile and empty_tile facts
        tmp_prolog_statements += "non_empty_tile(X,Y) :- assignment(X,Y,%s).\n " % ';'.join(non_empty_tile_ids)
        tmp_prolog_statements += "empty_tile(X,Y) :- tile(X,Y), not non_empty_tile(X,Y).\n"

        # Force specified tile coords to be certain tile types
        for tile_type, tile_coords in self.forced_tiles.items():

            if tile_type == 'empty':
                for x, y in tile_coords:
                    tmp_prolog_statements += ":- assignment(%d,%d,%s).\n" % (x, y, ';'.join(non_empty_tile_ids))

            elif tile_type == 'one_way_platform':
                for x, y in tile_coords:
                    tmp_prolog_statements += ":- not assignment(%d,%d,%s).\n" % (x, y, ';'.join(one_way_tile_ids))

            else:
                for x, y in tile_coords:
                    tmp_prolog_statements += "assignment(%d,%d,%s).\n" % (x, y, self.tile_ids.get(tile_type)[0])

        # Set floor tiles to be block tiles if pits are not allowed
        if not self.allow_pits:
            for x in range(self.level_w):
                floor_tile_assignment = "assignment(%d, %d, %s)." % (x, self.level_h-1, block_tile_id)
                tmp_prolog_statements += floor_tile_assignment + "\n"

        # Set start and goal tile index ranges (tile position ranges)
        start_tile_min_x, start_tile_max_x = self.tile_position_ranges.get('start_column')
        start_tile_min_y, start_tile_max_y = self.tile_position_ranges.get('start_row')
        goal_tile_min_x, goal_tile_max_x = self.tile_position_ranges.get('goal_column')
        goal_tile_min_y, goal_tile_max_y = self.tile_position_ranges.get('goal_row')

        tmp_prolog_statements += ":- assignment(X,Y,%s), X < %d.\n" % (start_tile_id, start_tile_min_x)
        tmp_prolog_statements += ":- assignment(X,Y,%s), X > %d.\n" % (start_tile_id, start_tile_max_x)
        tmp_prolog_statements += ":- assignment(X,Y,%s), Y < %d.\n" % (start_tile_id, start_tile_min_y)
        tmp_prolog_statements += ":- assignment(X,Y,%s), Y > %d.\n" % (start_tile_id, start_tile_max_y)

        tmp_prolog_statements += ":- assignment(X,Y,%s), X < %d.\n" % (goal_tile_id, goal_tile_min_x)
        tmp_prolog_statements += ":- assignment(X,Y,%s), X > %d.\n" % (goal_tile_id, goal_tile_max_x)
        tmp_prolog_statements += ":- assignment(X,Y,%s), Y < %d.\n" % (goal_tile_id, goal_tile_min_y)
        tmp_prolog_statements += ":- assignment(X,Y,%s), Y > %d.\n" % (goal_tile_id, goal_tile_max_y)

        # Force specified tiles to be reachable
        for x, y in self.reachable_tiles:
            tmp_prolog_statements += ":- not reachable_tile(%d,%d).\n" % (x, y)

        # Set num tile ranges
        for tile_type, tile_range in self.num_tile_ranges.items():
            if tile_type == 'empty':
                tmp_prolog_statements += "%d { empty_tile(X,Y) } %d.\n" % (tile_range[0], tile_range[1])

            elif tile_type == 'one_way':
                tmp_prolog_statements += "%d { one_way_tile(X,Y) } %d.\n" % (tile_range[0], tile_range[1])

            else:
                tmp_prolog_statements += "limit(%s,%d,%d).\n" % (self.tile_ids.get(tile_type)[0], tile_range[0], tile_range[1])

        # Set perc tile ranges
        for tile_type, tile_perc_range in self.perc_tile_ranges.items():
            if tile_type == 'empty':
                tmp_prolog_statements += "%d { empty_tile(X,Y) } %d.\n" % (int(tile_perc_range[0] / 100 * num_total_tiles),
                                                                           int(tile_perc_range[1] / 100 * num_total_tiles))

            elif tile_type == 'one_way':
                tmp_prolog_statements += "%d { one_way_tile(X,Y) } %d.\n" % (int(tile_perc_range[0] / 100 * num_total_tiles),
                                                                             int(tile_perc_range[1] / 100 * num_total_tiles))
            else:
                tmp_prolog_statements += "limit(%s,%d,%d).\n" % (self.tile_ids.get(tile_type)[0],
                                                                 int(tile_perc_range[0] / 100 * num_total_tiles),
                                                                 int(tile_perc_range[1] / 100 * num_total_tiles))

        # Remove duplicate lines
        self.tmp_prolog_statements = get_unique_lines(tmp_prolog_statements)
        return True

    def solve(self, max_sol, threads):
        self.stopwatch.start()
        seeds = random.sample(range(1, 999999), max_sol)
        print("SEEDS: %s" % str(seeds))

        for seed in seeds:
            prg = clingo.Control([])
            prg.configuration.solve.models = 1  # get one solution per seed
            prg.configuration.solve.parallel_mode = threads  # number of threads to use for solving
            prg.configuration.solver.sign_def = 'rnd'  # turn off default sign heuristic and switch to random signs
            prg.configuration.solver.seed = seed  # seed to use for solving

            print("----- LOADING -----")
            print("Loading prolog file: %s..." % self.prolog_file)
            prg.load(self.prolog_file)
            print(self.stopwatch.get_lap_time_str("Load prolog file"))

            print("Adding %d tmp_prolog_statements..." % (len(self.tmp_prolog_statements.split("\n"))))
            with prg.builder() as builder:
                clingo.parse_program(self.tmp_prolog_statements, lambda stm: builder.add(stm))
            print(self.stopwatch.get_lap_time_str("Parse tmp prolog statements"))

            prg.add('base', [], "")

            print("----- GROUNDING -----")
            print("Start: %s" % str(datetime.now()))
            prg.ground([('base', [])])
            print(self.stopwatch.get_lap_time_str("Ground"))

            print("----- SOLVING (%d/%d) -----" % (self.answer_set_count, max_sol-1))
            print("Start: %s" % str(datetime.now()))
            prg.solve(on_model=lambda m: self.process_answer_set(repr(m)))
            print(self.stopwatch.get_lap_time_str("Solve"))

        self.stopwatch.stop()

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
        for tile_type, tile_ids in self.tile_ids.items():
            if tile_id in tile_ids:
                return list(TILE_CHARS[tile_type].keys())[0]  # start, goal, block, bonus, one-way
        return list(TILE_CHARS['empty'].keys())[0]  # empty

    def get_facts_as_list(self, model_str, fact_name):
        return re.findall(r'%s\([0-9t,]*\)' % fact_name, model_str)

    def get_fact_coord(self, model_str, fact_name):
        facts = self.get_facts_as_list(model_str, fact_name)
        if len(facts) == 0:
            error_exit("'%s' fact not found in solver output" % fact_name)
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

            # Initialize num tiles dictionary
            num_tiles_dict = {'total': 0}  # total
            for tile_type in self.tile_ids.keys():  # start, goal, block, bonus, one-way
                num_tiles_dict[tile_type] = 0

            # Update num tiles dictionary values
            for (tile_id, extra_info), coords in tile_id_extra_info_coords_map.items():
                len_coords = len(coords)
                num_tiles_dict['total'] += len_coords  # update num total tiles

                for tile_type, tile_ids in self.tile_ids.items():
                    if tile_id in tile_ids:
                        num_tiles_dict[tile_type] += len_coords  # update num <tile-type> tiles

            for tile_type, count in num_tiles_dict.items():
                print("%s tiles: %d (%d%%)" % (tile_type, count, count / num_tiles_dict['total'] * 100))

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

        if self.print:
            print(level_structural_txt)

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
            print("Config: %s" % self.config_filename)
            print("Levels generated: %d" % self.answer_set_count)
            print("Valid levels : %d" % valid_level_count)
            print("Invalid levels: %d" % invalid_level_count)

        return True

