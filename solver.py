"""
Solver Object
"""

import clingo
import re
import networkx as nx
import random
from datetime import datetime
import time

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
        self.forced_tiles = config.get('forced_tiles')                          # { type: list-of-tile-coords }
        self.num_tiles = config.get('num_tiles')                                # { type: target_count }
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
        self.start_time = str(time.time())

    @staticmethod
    def parse_prolog_filepath(prolog_filepath):
        match = re.match('level_saved_files_([^/]+)/prolog_files/([a-zA-Z0-9_\-]+)\.pl', prolog_filepath)
        player_img = match.group(1)
        prolog_filename = match.group(2)
        return player_img, prolog_filename

    def increment_answer_set_count(self):
        self.answer_set_count += 1

    def get_cur_answer_set_filename(self, prolog_filename):
        filename_components = [prolog_filename, self.config_filename, "a%d" % self.answer_set_count, self.start_time]
        return "_".join(filename_components)

    def init_tmp_prolog_statements(self):
        tmp_prolog_statements = ""
        tmp_prolog_statements += "dim_width(0..%d).\n" % (self.level_w - 1)
        tmp_prolog_statements += "dim_height(0..%d).\n" % (self.level_h - 1)

        # ---- CREATE TILE FACTS ----
        create_tiles_statement = "tile(TX,TY) :- dim_width(TX), dim_height(TY)."
        tmp_prolog_statements += create_tiles_statement + "\n"

        # ----- GET TILE IDS FOR TILE TYPES -----
        start_tile_id = self.tile_ids.get('start')[0]
        goal_tile_id = self.tile_ids.get('goal')[0]

        prolog_tile_ids = {
            'block': ';'.join(self.tile_ids.get('block')),
            'bonus': ';'.join(self.tile_ids.get('bonus')),
            'hazard': ';'.join(self.tile_ids.get('hazard')),
            'wall': ';'.join(self.tile_ids.get('wall')),
            'one_way_platform': ';'.join(self.tile_ids.get('one_way_platform')),
            'permeable_wall': ';'.join(self.tile_ids.get('permeable_wall'))
        }

        level_has_tile_type = {
            'block': prolog_tile_ids.get('block') != '',
            'bonus': prolog_tile_ids.get('bonus') != '',
            'hazard': prolog_tile_ids.get('hazard') != '',
            'wall': prolog_tile_ids.get('wall') != '',
            'one_way_platform': prolog_tile_ids.get('one_way_platform') != '',
            'permeable_wall': prolog_tile_ids.get('permeable_wall') != ''
        }

        # ----- ADD BORDER TILE RULES -----
        if level_has_tile_type.get('wall') or level_has_tile_type.get('permeable_wall'):

            # Border tiles must be wall tiles
            tmp_prolog_statements += "assignment(X,Y,MT) :- tile(X,Y), Y==(0), MT==(%s).\n" % (prolog_tile_ids.get('wall'))
            tmp_prolog_statements += "assignment(X,Y,MT) :- tile(X,Y), Y==(%d), MT==(%s).\n" % (self.level_h - 1, prolog_tile_ids.get('wall'))

            if not level_has_tile_type.get('permeable_wall'):
                tmp_prolog_statements += "assignment(X,Y,MT) :- tile(X,Y), X==(0), MT==(%s).\n" % (prolog_tile_ids.get('wall'))
                tmp_prolog_statements += "assignment(X,Y,MT) :- tile(X,Y), X==(%d), MT==(%s).\n" % (self.level_w - 1, prolog_tile_ids.get('wall'))
            else:
                allowed_wall_tile_ids_str = ["ID != %s" % tile_id for tile_id in self.tile_ids.get("permeable_wall")]
                tmp_prolog_statements += ":- tile(X,Y), assignment(X,Y,ID), X==(0;%d), Y>0, Y<%d, %s.\n" % (
                    self.level_w-1, self.level_h-1, ','.join(allowed_wall_tile_ids_str)
                )

            # Non-border tiles cannot be wall tiles or permeable_wall tiles
            tmp_prolog_statements += ":- assignment(X,Y,ID), tile(X,Y), ID==(%s), X>0, X<%d, Y>0, Y<%d.\n" % (
                prolog_tile_ids.get('wall'), self.level_w - 1, self.level_h - 1)

            if level_has_tile_type.get('permeable_wall'):
                tmp_prolog_statements += ":- assignment(X,Y,ID), tile(X,Y), ID==(%s), X>0, X<%d, Y>0, Y<%d.\n" % (
                    prolog_tile_ids.get('permeable_wall'), self.level_w - 1, self.level_h - 1
                )

        # ----- ADD REACHABILITY RULES -----
        generic_state = State.generic_prolog_contents()

        # Non-block and non-goal tiles on top of block tiles must have a reachable ground state in them
        if self.require_all_platforms_reachable:

            reachable_platform_ids = prolog_tile_ids.get('block') if not level_has_tile_type.get('one_way_platform') \
                else ';'.join([prolog_tile_ids.get('block'), prolog_tile_ids.get('one_way_platform')])

            tmp_prolog_statements += "tile_above_block(TX,TY) :- tile(TX,TY), assignment(TX,TY,ID1), ID1 != %s, ID1 != %s, ID1 != %s, tile(TX,TY+1), assignment(TX,TY+1,ID2), ID2 == (%s).\n" % \
                                     (goal_tile_id, prolog_tile_ids.get('block'), prolog_tile_ids.get('wall'), reachable_platform_ids)
            tmp_prolog_statements += "tile_has_reachable_ground_state(TX,TY) :- tile(TX,TY), reachable(%s), %s, TX==X/%d, TY==Y/%d.\n"  % (generic_state, State.generic_ground_reachability_expression(), TILE_DIM, TILE_DIM)
            tmp_prolog_statements += ":- tile_above_block(TX,TY), not tile_has_reachable_ground_state(TX,TY).\n"

        # Bonus tiles must have a reachable bonus state in the tile below them
        if self.require_all_bonus_tiles_reachable and level_has_tile_type.get('bonus'):
            tmp_prolog_statements += "tile_below_bonus(TX,TY) :- tile(TX,TY), tile(TX,TY-1), assignment(TX,TY-1,%s).\n" % prolog_tile_ids.get('bonus')
            tmp_prolog_statements += "tile_has_reachable_bonus_state(TX,TY) :- tile(TX,TY), reachable(%s), %s, TX==X/%d, TY==Y/%d.\n" % (
                generic_state, State.generic_bonus_reachability_expression(), TILE_DIM, TILE_DIM
            )
            tmp_prolog_statements += ":- tile_below_bonus(TX,TY), not tile_has_reachable_bonus_state(TX,TY).\n"

        # ----- ADD START/GOAL ON_GROUND RULES -----

        allowed_ground_tile_ids = self.tile_ids.get('block')
        if level_has_tile_type.get('one_way_platform'):
            allowed_ground_tile_ids += self.tile_ids.get('one_way_platform')

        allowed_ground_tile_ids_str = ','.join(["ID != %s" % tile_id for tile_id in allowed_ground_tile_ids])

        if self.require_start_on_ground:
            tmp_prolog_statements += ":- tile(X,Y), tile(X,Y+1), assignment(X,Y,%s), assignment(X,Y+1,ID), " \
                                     "metatile(ID), %s.\n" % (start_tile_id, allowed_ground_tile_ids_str)

        if self.require_goal_on_ground:
            tmp_prolog_statements += ":- tile(X,Y), tile(X,Y+1), assignment(X,Y,%s), assignment(X,Y+1,ID), " \
                                     "metatile(ID), %s.\n" % (goal_tile_id, allowed_ground_tile_ids_str)

        # ----- SET START/GOAL TILE INDEX POSITION RANGES
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

        # ----- SET UP NUM_TILE TARGET COUNTS -----
        if len(self.num_tiles) > 0:

            tmp_prolog_statements += "total_penalty(T) :- T = #sum { P : penalty(P) }.\n"
            tmp_prolog_statements += "#minimize { T, T : total_penalty(T) }.\n"

            for tile_type, target_count in self.num_tiles.items():

                if target_count is not None and level_has_tile_type.get(tile_type):
                    range_threshold = int(target_count * 0.20)  # stay within 20% range of target count

                    tmp_prolog_statements += "%s_count(C) :- C = #count { assignment(X,Y,MT) : metatile(MT), " \
                                             "tile(X,Y), MT==(%s) }.\n" % (tile_type, prolog_tile_ids.get("%s" % tile_type))
                    tmp_prolog_statements += "penalty(P) :- P = #max { 0; |%d - C|-%d : %s_count(C) }.\n" % \
                                             (target_count, range_threshold, tile_type)

        # ----- ENFORCE PERC_LEVEL_RANGES -----
        # if use_soft_constraints and self.soft_constraints.get('perc_level_ranges'):
        #     pass  # TODO implement
        # else:
        #     # Create level_assignment facts to track which tiles came from which training levels
        #     for level, tile_ids in self.level_ids_map.items():
        #         tmp_prolog_statements += "level_assignment(\"%s\",X,Y) :- tile(X,Y), assignment(X,Y,ID), ID==(%s).\n" % (
        #             level, ';'.join(tile_ids))
        #
        #     # Set perc level ranges (e.g. 50-100% tiles must come from level 1)
        #     for level, tile_perc_range in self.perc_level_ranges.items():
        #         min_tiles = int(tile_perc_range[0] / 100 * num_total_tiles)
        #         max_tiles = int(tile_perc_range[1] / 100 * num_total_tiles)
        #         level_perc_range_rule = "%d { level_assignment(\"L\",X,Y) : tile(X,Y), L==(%s) } %d.\n" % (
        #             min_tiles, level, max_tiles)
        #         tmp_prolog_statements += level_perc_range_rule

        # # Force specified tile coords to be certain tile types
        # for tile_type, tile_coords in self.forced_tiles.items():
        #
        #     if tile_type == 'empty':
        #         for x, y in tile_coords:
        #             tmp_prolog_statements += ":- assignment(%d,%d,%s).\n" % (x, y, ';'.join(non_empty_tile_ids))
        #
        #     elif tile_type == 'one_way_platform':
        #         for x, y in tile_coords:
        #             tmp_prolog_statements += ":- not assignment(%d,%d,%s).\n" % (x, y, ';'.join(one_way_tile_ids))
        #
        #     else:
        #         for x, y in tile_coords:
        #             tmp_prolog_statements += "assignment(%d,%d,%s).\n" % (x, y, self.tile_ids.get(tile_type)[0])

        # ----- REMOVE DUPLICATE PROLOG LINES -----
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
    def get_facts_as_list(model_str, fact_name):
        facts = re.findall(r'[\s^]%s\([^\)]+\)' % fact_name, model_str)
        facts = [fact.strip() for fact in facts]
        return facts

    @staticmethod
    def get_fact_contents_as_list(fact_str):  # reachable(X,Y,Z) => X,Y,Z
        match = re.match(r'[^\(]+\(([^\)]+)\)', fact_str)
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
            asp_valid = Solver.asp_is_valid(check_path=True,
                                            check_onground=self.require_all_platforms_reachable,
                                            check_bonus=self.require_all_bonus_tiles_reachable,
                                            model_str=model_str,
                                            player_img=player_img,
                                            answer_set_filename=answer_set_filename,
                                            tile_ids=self.tile_ids.copy(),
                                            save=self.save)
            self.asp_valid_levels_count += 1 if asp_valid else 0

            # state_graph_valid_path = Solver.get_state_graph_valid_path(assignments_dict, player_img, prolog_filename,
            #                                                            answer_set_filename, save=self.save)
            # self.state_graph_valid_levels_count += 1 if state_graph_valid_path is not None else 0

        self.increment_answer_set_count()

    @staticmethod
    def asp_is_valid(check_path, check_onground, check_bonus, model_str, player_img, answer_set_filename, tile_ids, save):

        asp_validation_checks = []

        if check_path:
            # Check valid path from start to goal state
            asp_valid_path = Solver.get_asp_valid_path(model_str, player_img, answer_set_filename, save)
            asp_validation_checks.append(asp_valid_path)

            if not all([asp_valid_path]):
                print("%s: VALID PATH CHECK FAILED" % answer_set_filename)

        if check_onground or check_bonus:

            # Get tile_ids
            block_tile_id = tile_ids.get('block')[0]
            goal_tile_id = tile_ids.get('goal')[0]
            bonus_tile_id = None if len(tile_ids.get('bonus')) == 0 else tile_ids.get('bonus')[0]

            # Create assignments_dict from model_str {(tile_x, tile_y): tile_id}
            assignment_facts = Solver.get_facts_as_list(model_str, fact_name='assignment')
            assignments_dict = {}
            for assignment_fact in assignment_facts:
                tile_x, tile_y, tile_id = Solver.get_fact_contents_as_list(assignment_fact)
                tile_x, tile_y = int(tile_x), int(tile_y)
                assignments_dict[(tile_x, tile_y)] = tile_id

            # Get reachable fact contents from model_str
            reachable_facts = Solver.get_facts_as_list(model_str, fact_name='reachable')
            reachable_contents = [Solver.get_fact_contents_as_list(fact) for fact in reachable_facts]

            # Check that all platforms are reachable
            if check_onground:
                ground_states_reachable = Solver.all_ground_states_reachable(assignments_dict, reachable_contents,
                                                                             block_tile_id=block_tile_id,
                                                                             goal_tile_id=goal_tile_id)
                asp_validation_checks.append(ground_states_reachable)

                if not all([ground_states_reachable]):
                    print("%s: ON GROUND CHECK FAILED" % answer_set_filename)

            # Check that all bonus tiles are collectable
            if check_bonus:
                if bonus_tile_id is not None:
                    bonus_states_reachable = Solver.all_bonus_states_reachable(assignments_dict, reachable_contents,
                                                                               bonus_tile_id=bonus_tile_id)
                    asp_validation_checks.append(bonus_states_reachable)

                    if not all([bonus_states_reachable]):
                        print("%s: BONUS CHECK FAILED" % answer_set_filename)

        return all(asp_validation_checks)

    @staticmethod
    def all_ground_states_reachable(assignments_dict, reachable_contents, block_tile_id, goal_tile_id):

        # Get list of non-block/non-goal tiles on top of block tiles
        tiles_above_blocks = []
        for (tile_x, tile_y), tile_id in assignments_dict.items():
            if tile_id == block_tile_id and assignments_dict.get((tile_x, tile_y-1)) is not None:
                if assignments_dict.get((tile_x, tile_y-1)) not in [block_tile_id, goal_tile_id]:
                    tiles_above_blocks.append((tile_x, tile_y-1))

        # Create tile_with_reachable_ground_state_dict {(tile_x, tile_y): 1}
        tile_with_reachable_ground_state_dict = {}
        for reachable_content_list in reachable_contents:
            if reachable_content_list[State.prolog_state_contents_on_ground_index()] == '1':
                state_x = int(reachable_content_list[State.prolog_state_contents_x_index()])
                state_y = int(reachable_content_list[State.prolog_state_contents_y_index()])
                tile_with_reachable_ground_state_dict[(state_x // TILE_DIM, state_y // TILE_DIM)] = 1

        # Ensure that every tile_above_block has a reachable ground state
        for tile_x, tile_y in tiles_above_blocks:
            if tile_with_reachable_ground_state_dict.get((tile_x, tile_y)) is None:
                return False

        return True

    @staticmethod
    def all_bonus_states_reachable(assignments_dict, reachable_contents, bonus_tile_id):

        # Get list of tiles below bonus tiles
        tiles_below_bonus = []
        for (tile_x, tile_y), tile_id in assignments_dict.items():
            if tile_id == bonus_tile_id and assignments_dict.get((tile_x, tile_y+1)) is not None:
                tiles_below_bonus.append((tile_x, tile_y+1))

        # Create tile_with_reachable_bonus_state_dict {(tile_x, tile_y}: 1}
        tile_with_reachable_bonus_state_dict = {}
        for reachable_content_list in reachable_contents:
            if reachable_content_list[State.prolog_state_contents_hit_bonus_coord_index()] != '':
                state_x = int(reachable_content_list[State.prolog_state_contents_x_index()])
                state_y = int(reachable_content_list[State.prolog_state_contents_y_index()])
                tile_with_reachable_bonus_state_dict[(state_x//TILE_DIM, state_y//TILE_DIM)] = 1

        # Ensure that every tile_below_bonus has a reachable bonus state
        for tile_x, tile_y in tiles_below_bonus:
            if tile_with_reachable_bonus_state_dict.get((tile_x, tile_y)) is None:
                return False

        return True

    @staticmethod
    def get_asp_valid_path(model_str, player_img, answer_set_filename, save=True):
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
                    valid_path = nx.dijkstra_path(graph, source=start_node, target=goal_node)
                    if save:
                        valid_path_str = " => \n".join(valid_path)
                        valid_path_file = get_filepath("level_saved_files_%s/generated_level_paths" % player_img, "%s.pickle" % answer_set_filename)
                        write_pickle(valid_path_file, valid_path_str)
                    return valid_path

        return None

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
    def get_state_graph_valid_path(assignments_dict, player_img, prolog_filename, answer_set_filename, save=True):

        # Construct state graph for generated level
        id_metatile_file = "level_saved_files_%s/id_metatile_maps/%s.pickle" % (player_img, prolog_filename)
        state_graph = Solver.construct_state_graph(assignments_dict, id_metatile_file)
        if save:
            state_graph_file = get_filepath('level_saved_files_%s/enumerated_state_graphs/generated' % player_img, '%s.gpickle' % answer_set_filename)
            nx.write_gpickle(state_graph, state_graph_file)

        # Check for valid path from start to goal state
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
                    return nx.dijkstra_path(state_graph, source=start_node, target=goal_node)

        return None

    def end_and_validate(self):
        print("----- SUMMARY -----")
        print("Generated Levels: %d" % self.answer_set_count)

        if self.validate:
            print("ASP validated levels: %d" % self.asp_valid_levels_count)
            print('State graph validated levels: %d' % self.state_graph_valid_levels_count)

        return True
