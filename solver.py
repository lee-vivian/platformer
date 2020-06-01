"""
Solver Object
"""

import clingo
import re
import networkx as nx
import random
from datetime import datetime

from model.level import TILE_DIM, TILE_CHARS
from model.metatile import Metatile
from model_platformer.state import StatePlatformer as State
from stopwatch import Stopwatch
from utils import get_filepath, read_pickle, write_pickle, write_file, error_exit, get_unique_lines


class Solver:

    def __init__(self, prolog_file, config, config_filename, tile_ids, level_ids_map, print_level, save, validate):
        self.prolog_file = prolog_file
        self.config_filename = config_filename
        self.level_w = config.get('level_w')
        self.level_h = config.get('level_h')
        self.forced_tiles = config.get('forced_tiles')                          # {type: list-of-tile-coords}
        self.num_tile_ranges = config.get('num_tile_ranges')                    # { type: (min, max) }
        self.perc_tile_ranges = config.get('perc_tile_ranges')                  # { type: (min, max) }
        self.perc_level_ranges = config.get('perc_level_ranges')                # { level: (min, max) }
        self.tile_position_ranges = config.get('tile_position_ranges')          # { position: (min, max) }
        self.require_start_on_ground = config.get('require_start_on_ground')    # bool
        self.require_goal_on_ground = config.get('require_goal_on_ground')      # bool
        self.num_gaps_range = config.get('num_gaps_range')                      # (min, max)
        self.require_all_platforms_reachable = config.get('require_all_platforms_reachable')  # bool
        self.require_all_bonus_tiles_reachable = config.get('require_all_bonus_tiles_reachable')  # bool
        self.tile_ids = tile_ids                                                # { tile_type: list-of-tile-ids }
        self.level_ids_map = level_ids_map                                      # { level: list-of-tile-ids }
        self.print_level = print_level
        self.save = save
        self.validate = validate
        self.tmp_prolog_statements = ""
        self.init_tmp_prolog_statements()  # create tmp prolog statements
        self.answer_set_count = 0
        self.asp_valid_levels_count = 0
        self.state_graph_valid_levels_count = 0
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
        filename_components = [prolog_filename, self.config_filename, "a%d" % self.answer_set_count]
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
        bonus_tile_id = None if len(self.tile_ids.get('bonus')) == 0 else self.tile_ids.get('bonus')[0]

        # Add border tile rules if wall tiles exist
        if len(self.tile_ids.get('wall')) > 0:
            wall_tile_id = self.tile_ids.get('wall')[0]

            # Border tiles must be wall tiles
            tmp_prolog_statements += "assignment(X,Y,%s) :- tile(X,Y), X==(0).\n" % (wall_tile_id,)
            tmp_prolog_statements += "assignment(X,Y,%s) :- tile(X,Y), X==(%d).\n" % (wall_tile_id, self.level_w - 1)
            tmp_prolog_statements += "assignment(X,Y,%s) :- tile(X,Y), Y==(0).\n" % (wall_tile_id,)
            tmp_prolog_statements += "assignment(X,Y,%s) :- tile(X,Y), Y==(%d).\n" % (wall_tile_id, self.level_h - 1)

            # Non-border tiles cannot be wall tiles
            tmp_prolog_statements += ":- assignment(X,Y,ID), tile(X,Y), ID==%s, X>0, X<%d, Y>0, Y<%d.\n" % (
                wall_tile_id, self.level_w - 1, self.level_h - 1)

        # Add rules for enforcing reachable states
        generic_state = State.generic_prolog_contents()

        if self.require_all_platforms_reachable:
            tmp_prolog_statements += ":- state(%s), not reachable(%s), %s.\n" % (generic_state, generic_state, State.generic_ground_reachability_expression())

        if self.require_all_bonus_tiles_reachable:
            tmp_prolog_statements += ":- state(%s), not reachable(%s), %s.\n" % (generic_state, generic_state, State.generic_bonus_reachability_expression())

        # Create one_way facts for one_way_platform tile assignments
        if len(one_way_tile_ids) > 0:
            tmp_prolog_statements += "one_way_tile(X,Y) :- tile(X,Y), assignment(X,Y,ID), ID=(%s).\n" % (';'.join(one_way_tile_ids))

        # Create level_assignment facts
        for level, tile_ids in self.level_ids_map.items():
            level_assignment_fact = "level_assignment(\"%s\",X,Y) :- tile(X,Y), assignment(X,Y,ID), ID=(%s)." % (level, ';'.join(tile_ids))
            tmp_prolog_statements += level_assignment_fact + "\n"

        # Get non-empty tile ids
        non_empty_tile_ids = []
        for tile_type, tile_ids in self.tile_ids.items():
            non_empty_tile_ids += tile_ids

        # Create non_empty_tile facts
        tmp_prolog_statements += "non_empty_tile(X,Y) :- tile(X,Y), assignment(X,Y,ID), ID=(%s).\n " % (';'.join(non_empty_tile_ids))

        # Create gap_tile facts (if floor tile has type = empty)
        tmp_prolog_statements += "gap_tile(X,Y) :- tile(X,Y), Y=%d, assignment(X,Y,ID), ID!=(%s).\n" % (self.level_h-1, ';'.join(non_empty_tile_ids))

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

        # Require start tile to be on ground (start tile must be on top of a block tile)
        if self.require_start_on_ground:
            start_on_ground_rule = ":- assignment(X,Y,%s), not assignment(X,Y+1,%s)." % (start_tile_id, block_tile_id)
            tmp_prolog_statements += start_on_ground_rule + "\n"

        # Require goal tile to be on ground (goal tile must be on top of a block tile)
        if self.require_goal_on_ground:
            goal_on_ground_rule = ":- assignment(X,Y,%s), not assignment(X,Y+1,%s)." % (goal_tile_id, block_tile_id)
            tmp_prolog_statements += goal_on_ground_rule + "\n"

        # Set range number of gaps allowed in a valid level
        min_num_gaps, max_num_gaps = self.num_gaps_range
        tmp_prolog_statements += "%d { gap_tile(X,Y) : tile(X,Y) } %d.\n" % (min_num_gaps, max_num_gaps)

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

        # Set perc level ranges (e.g. 50-100% tiles must come from level 1)
        for level, tile_perc_range in self.perc_level_ranges.items():
            min_tiles = int(tile_perc_range[0] / 100 * num_total_tiles)
            max_tiles = int(tile_perc_range[1] / 100 * num_total_tiles)
            level_perc_range_rule = "%d { level_assignment(L,X,Y) : tile(X,Y), L=\"%s\" } %d.\n" % (min_tiles, level, max_tiles)
            tmp_prolog_statements += level_perc_range_rule

        # Set num tile ranges
        for tile_type, tile_range in self.num_tile_ranges.items():

            if tile_type == 'empty':
                min_empty, max_empty = tile_range
                min_non_empty = num_total_tiles - max_empty
                max_non_empty = num_total_tiles - min_empty
                tmp_prolog_statements += "%d { non_empty_tile(X,Y) : tile(X,Y) } %d.\n" % (min_non_empty, max_non_empty)

            elif tile_type == 'one_way_platform':
                tmp_prolog_statements += "%d { one_way_tile(X,Y) : tile(X,Y) } %d.\n" % (tile_range[0], tile_range[1])

            else:
                tile_ids = self.tile_ids.get(tile_type)
                if len(tile_ids) > 0:
                    tmp_prolog_statements += "limit(%s,%d,%d).\n" % (self.tile_ids.get(tile_type)[0], tile_range[0], tile_range[1])

        # Set perc tile ranges
        for tile_type, tile_perc_range in self.perc_tile_ranges.items():

            if tile_type == 'empty':
                min_perc_empty, max_perc_empty = tile_perc_range
                min_perc_non_empty = 100 - max_perc_empty
                max_perc_non_empty = 100 - min_perc_empty
                tmp_prolog_statements += "%d { non_empty_tile(X,Y) : tile(X,Y) } %d.\n" % (min_perc_non_empty / 100 * num_total_tiles,
                                                                                           max_perc_non_empty / 100 * num_total_tiles)

            elif tile_type == 'one_way_platform':
                tmp_prolog_statements += "%d { one_way_tile(X,Y) : tile(X,Y) } %d.\n" % (int(tile_perc_range[0] / 100 * num_total_tiles),
                                                                                         int(tile_perc_range[1] / 100 * num_total_tiles))

            else:
                tile_ids = self.tile_ids.get(tile_type)
                if len(tile_ids) > 0:
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

    def get_tile_char(self, tile_id):
        for tile_type, tile_ids in self.tile_ids.items():
            if tile_id in tile_ids:
                return list(TILE_CHARS[tile_type].keys())[0]  # start, goal, block, bonus, one-way
        return list(TILE_CHARS['empty'].keys())[0]  # empty

    @staticmethod
    def create_assignments_dict(model_str):
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
    def construct_state_graph(assignments_dict, id_metatile_file):
        id_metatile_map = read_pickle(id_metatile_file)
        state_graph = nx.DiGraph()
        for (tile_x, tile_y), tile_id in assignments_dict.items():
            metatile = Metatile.from_str(id_metatile_map.get(tile_id))
            metatile_graph = nx.DiGraph(metatile.graph_as_dict)
            if nx.is_empty(metatile_graph):
                pass
            else:
                unnormalized_graph = Metatile.get_normalized_graph(metatile_graph,
                                                                   coord=(tile_x*TILE_DIM, tile_y*TILE_DIM),
                                                                   normalize=False)
                state_graph = nx.compose(state_graph, unnormalized_graph)

        return state_graph

    @staticmethod
    def get_facts_as_list(model_str, fact_name):
        return re.findall(r'%s\([^\)]+\).' % fact_name, model_str)

    @staticmethod
    def get_fact_contents_as_list(fact_str):  # reachable(X,Y,Z) => X,Y,Z
        match = re.match(r'[a-zA-Z_]+\(([^\)]+)\)\s', fact_str)
        match = match.group(1)
        return match.split(',')

    def process_answer_set(self, model_str):
        player_img, prolog_filename = Solver.parse_prolog_filepath(self.prolog_file)
        answer_set_filename = self.get_cur_answer_set_filename(prolog_filename)

        # Create assignments dictionary {(tile_x, tile_y): tile_id}
        assignments_dict = Solver.create_assignments_dict(model_str)

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

            generated_level_assignments_dir = "level_saved_files_%s/generated_level_assignments_dicts/" % player_img
            level_assignments_file = get_filepath(generated_level_assignments_dir, "%s.pickle" % answer_set_filename)
            write_pickle(level_assignments_file, assignments_dict)

            generated_level_model_str_dir = "level_saved_files_%s/generated_level_model_strs/" % player_img
            level_model_str_file = get_filepath(generated_level_model_str_dir, "%s.txt" % answer_set_filename)
            write_pickle(level_model_str_file, model_str)

        if self.print_level:
            print(level_structural_txt)

        if self.validate:

            # Check ASP model output for valid path
            asp_valid_path = Solver.get_asp_valid_path(model_str)
            self.asp_valid_levels_count += 1 if asp_valid_path is not None else 0
            if asp_valid_path is not None and self.save:
                valid_path_file = get_filepath('level_saved_files_%s/generated_level_paths' % player_img, '%s.pickle' % answer_set_filename)
                write_pickle(valid_path_file, asp_valid_path)

            # Construct state graph and check for valid path
            id_metatile_file = "level_saved_files_%s/id_metatile_maps/%s.pickle" % (player_img, prolog_filename)
            state_graph = Solver.construct_state_graph(assignments_dict, id_metatile_file)
            state_graph_has_valid_path = Solver.check_state_graph_valid_path(state_graph)
            self.state_graph_valid_levels_count += 1 if state_graph_has_valid_path else 0
            if self.save:
                state_graph_file = get_filepath('level_saved_files_%s/enumerated_state_graphs/generated' % player_img,'%s.gpickle' % answer_set_filename)
                nx.write_gpickle(state_graph, state_graph_file)

        self.increment_answer_set_count()

    @staticmethod
    def get_asp_valid_path(model_str):
        # Initialize start and goal fact variables
        start_nodes = []
        goal_nodes = []
        is_start_idx = State.prolog_state_contents_is_start_index()
        goal_reached_idx = State.prolog_state_contents_goal_reached_index()

        # Create new graph for model
        graph = nx.Graph()

        # Add nodes from reachable facts
        reachable_facts = Solver.get_facts_as_list(model_str, fact_name='reachable')

        for reachable_fact in reachable_facts:
            reachable_contents = Solver.get_fact_contents_as_list(reachable_fact)
            reachable_node = str(reachable_contents)
            graph.add_node(reachable_node)
            if reachable_contents[is_start_idx] == '1':
                start_nodes.append(reachable_node)
            if reachable_contents[goal_reached_idx] == '1':
                goal_nodes.append(reachable_node)

        # Check that reachable start and goal states exist
        if len(start_nodes) == 0:
            error_exit('No reachable start states found in model str')
        if len(goal_nodes) == 0:
            error_exit('No reachable goal states found in model str')

        # Add edges from link facts
        link_facts = Solver.get_facts_as_list(model_str, fact_name='link')
        for link_fact in link_facts:
            link_contents = Solver.get_fact_contents_as_list(link_fact)
            src_node = str(link_contents[:len(link_contents)//2])
            dest_node = str(link_contents[len(link_contents)//2:])
            graph.add_edge(src_node, dest_node)

        # Check if valid path exists from start to goal
        for start_node in start_nodes:
            for goal_node in goal_nodes:
                valid_path_exists = nx.has_path(graph, source=start_node, target=goal_node)
                if valid_path_exists:
                    return nx.dijkstra_path(graph, source=start_node, target=goal_node)

        return None

    @staticmethod
    def check_state_graph_valid_path(state_graph):
        start_nodes = []
        goal_nodes = []

        for node in state_graph.nodes():
            state = State.from_str(node)
            if state.is_start:
                start_nodes.append(node)
            if state.goal_reached:
                goal_nodes.append(node)

        if len(start_nodes) == 0:
            error_exit("No start states found in generated level state graph")

        if len(goal_nodes) == 0:
            error_exit("No goal states found in generated level state graph")

        for start_node in start_nodes:
            for goal_node in goal_nodes:
                if nx.has_path(state_graph, source=start_node, target=goal_node):
                    return True

        return False

    def end_and_validate(self):
        print("----- SUMMARY -----")
        print("Generated Levels: %d" % self.answer_set_count)

        if self.validate:
            print("ASP validated levels: %d" % self.asp_valid_levels_count)
            print('State graph validated levels: %d' % self.state_graph_valid_levels_count)

        return True

