"""
Acknowledgements and References:
- Legal adjacency rules based on NPCDev groundcollapse
- WFC in ASP implementation: based on Karth, I., & Smith, A. M. (2017). WaveFunctionCollapse is constraint solving
  in the wild. Proceedings of the 12th International Conference on the Foundations of Digital Games, 68. ACM.
"""

import networkx as nx
import re
import subprocess
import sys
import os
import argparse

from model.level import TILE_DIM, TILE_CHARS
from model_platformer.state import StatePlatformer as State
from model.metatile import METATILE_TYPES
import utils

import pdb

GENERATED_LEVELS_DIR = 'level_structural_layers/generated'
GENERATED_ASSIGNMENTS_DICTS_DIR = 'level_saved_files_block/generated_model_assignments_dicts'


def parse_constraints_filepath(constraints_filename):
    match = re.match(r'([^/]+)/metatile_constraints/([a-zA-Z0-9_-]+).pickle', constraints_filename)
    level_saved_files_dir = match.group(1)
    prolog_filename = match.group(2)
    return level_saved_files_dir, prolog_filename


def general_prolog_statements(tile_constraints_file):

    prolog_statements = ""

    # Load in tile_id constraints
    tile_id_constraints_dict = utils.read_pickle(tile_constraints_file)

    # Create general prolog statements for the training level
    prolog_statements += "dim_metatiles(1..%d).\n" % len(tile_id_constraints_dict)

    # Limit num metatile assignments per tile
    min_assignments = 1
    prolog_statements += "%d {assignment(TX, TY, MT) : metatile(MT) } 1 :- tile(TX,TY).\n" % min_assignments

    # Create tile adjacency rules
    adj_rule_prefix = "adj(X1,Y1,X2,Y2,DX,DY) :- tile(X1,Y1), tile(X2,Y2), X2-X1 == DX, Y2-Y1 == DY"
    horizontal_adj_rule = "%s, |DX| == 1, DY == 0." % adj_rule_prefix
    vertical_adj_rule = "%s, DX == 0, |DY| == 1." % adj_rule_prefix
    diagonal_adj_rule = "%s, |DX| == 1, |DY| == 1." % adj_rule_prefix
    prolog_statements += horizontal_adj_rule + "\n" + vertical_adj_rule + "\n" + diagonal_adj_rule + "\n"

    # Create {metatile_type: tile_ids} map
    metatile_type_ids_map = {}
    for t in METATILE_TYPES:
        metatile_type_ids_map[t] = []

    # Create {tile_id: {direction: set(neighbor_wfc_types)}} map
    tile_id_adjacent_types_map = {}
    empty_types_map = utils.list_to_dict(["start", "goal", "permeable_wall"])

    # Create {level: tile_ids} map
    metatile_level_ids_map = {}

    # Get generic state strs in prolog format
    generic_state = State.generic_prolog_contents()
    generic_src_state = State.generic_prolog_contents(index=1)
    generic_dest_state = State.generic_prolog_contents(index=2)

    # Add prolog facts and rules based on the given tile constraints
    for tile_id, tile_constraints in tile_id_constraints_dict.items():

        # Create metatile fact
        prolog_statements += "metatile(%s).\n" % tile_id

        # Populate {metatile_type: tile_ids} map
        metatile_type = tile_constraints.get('type')
        metatile_type_ids_map[metatile_type].append(tile_id)

        # Get wfc type of the current metatile
        wfc_type = metatile_type if empty_types_map.get(metatile_type) is None else "empty"
        prolog_statements += "wfc(%s, %s).\n" % (wfc_type, tile_id)

        # Update legal wfc tile_type neighbors
        metatile_adjacencies = tile_constraints.get('adjacent')
        for direction, neighbor_tile_ids in metatile_adjacencies.items():
            for neighbor_tile_id in neighbor_tile_ids:

                neighbor_type = tile_id_constraints_dict.get(neighbor_tile_id).get('type')
                neighbor_wfc_type = neighbor_type if empty_types_map.get(neighbor_type) is None else "empty"

                if tile_id_adjacent_types_map.get(tile_id) is None:
                    tile_id_adjacent_types_map[tile_id] = {}

                if tile_id_adjacent_types_map[tile_id].get(direction) is None:
                    tile_id_adjacent_types_map[tile_id][direction] = set()

                tile_id_adjacent_types_map[tile_id][direction].add(neighbor_wfc_type)

        # Populate {level: tile_ids} map
        metatile_levels = tile_constraints.get('levels')
        for level in metatile_levels:
            if metatile_level_ids_map.get(level) is None:
                metatile_level_ids_map[level] = [tile_id]
            else:
                metatile_level_ids_map[level].append(tile_id)

        # Retrieve the metatile graph
        metatile_graph = nx.DiGraph(tile_constraints.get('graph'))

        # Create state and link rules based on metatile graph
        for edge in metatile_graph.edges():
            src_state = State.from_str(edge[0])
            src_state_contents = src_state.to_prolog_contents()
            dest_state = State.from_str(edge[1])
            dest_state_contents = dest_state.to_prolog_contents()
            prolog_statements += "state(%s) :- assignment(TX,TY,%s), tile(TX,TY).\n" % (src_state_contents, tile_id)
            prolog_statements += "linkout(%s,%s) :- assignment(TX,TY,%s), tile(TX,TY).\n" % (
            src_state_contents, dest_state_contents, tile_id)
            prolog_statements += "linkin(%s,%s) :- assignment(TX,TY,%s), tile(TX,TY).\n" % (
            src_state_contents, dest_state_contents, tile_id)

    # Add rule for valid links
    prolog_statements += ":- linkout(%s,%s), state(%s), not state(%s).\n" % (
        generic_src_state, generic_dest_state, generic_src_state, generic_dest_state)
    prolog_statements += ":- linkout(%s,%s), not linkin(%s,%s), state(%s).\n" % (
        generic_src_state, generic_dest_state, generic_src_state, generic_dest_state, generic_src_state)
    prolog_statements += ":- linkin(%s,%s), state(%s), not state(%s).\n" % (
        generic_src_state, generic_dest_state, generic_dest_state, generic_src_state)
    prolog_statements += ":- linkin(%s,%s), not linkout(%s,%s), state(%s).\n" % (
        generic_src_state, generic_dest_state, generic_src_state, generic_dest_state, generic_dest_state)

    # Create legal adjacency prolog facts: legal(dx, dy, tile_id, neighbor_wfc_type)
    for tile_id, adjacency_dict in tile_id_adjacent_types_map.items():
        for direction, neighbor_wfc_types in adjacency_dict.items():
            for neighbor_wfc_type in neighbor_wfc_types:
                prolog_statements += "legal(%s,%s,%s,%s).\n" % (direction[0], direction[1], tile_id, neighbor_wfc_type)

    # Limit number of tiles of specified tile_id
    limit_tile_id_rule = "MIN { assignment(X,Y,MT) : metatile(MT), tile(X,Y) } MAX :- limit(MT, MIN, MAX)."
    prolog_statements += limit_tile_id_rule + "\n"
    prolog_statements += "limit(%s, 1, 1).\n" % metatile_type_ids_map.get('start')[0]
    prolog_statements += "limit(%s, 1, 1).\n" % metatile_type_ids_map.get('goal')[0]

    # Add state reachable rule
    state_reachable_rule = "reachable(%s) :- linkin(%s,%s), linkout(%s,%s), state(%s), state(%s), reachable(%s)." % (
        generic_dest_state, generic_src_state, generic_dest_state, generic_src_state, generic_dest_state,
        generic_src_state, generic_dest_state, generic_src_state
    )
    prolog_statements += state_reachable_rule + "\n"

    # Start states are inherently reachable
    prolog_statements += "reachable(%s) :- state(%s), %s.\n" % (
        generic_state, generic_state, State.generic_start_reachability_expression())

    # Goal states must be reachable
    prolog_statements += ":- state(%s), not reachable(%s), %s.\n" % (
        generic_state, generic_state, State.generic_goal_reachability_expression())

    # Get one_way_platform tile_ids
    one_way_platform_tile_ids = metatile_type_ids_map.get("one_way_platform")

    # ASP WFC algorithm rule
    wfc_rule = ":- adj(X1,Y1,X2,Y2,DX,DY), assignment(X1,Y1,MT1), assignment(X2,Y2,MT2), wfc(T1,MT1), " \
               "wfc(T2,MT2), not legal(DX,DY,MT1,T2)."
    prolog_statements += wfc_rule + "\n"

    # Remove duplicate prolog statements
    prolog_statements = utils.get_unique_lines(prolog_statements)

    # Create map of tile ids for each tile type
    tile_ids_map = {
        'block_tile_ids': metatile_type_ids_map.get('block'),
        'start_tile_ids': metatile_type_ids_map.get('start'),
        'goal_tile_ids': metatile_type_ids_map.get('goal'),
        'bonus_tile_ids': metatile_type_ids_map.get('bonus'),
        'one_way_platform_tile_ids': metatile_type_ids_map.get('one_way_platform'),
        'hazard_tile_ids': metatile_type_ids_map.get('hazard'),
        'wall_tile_ids': metatile_type_ids_map.get('wall'),
        'permeable_wall_tile_ids': metatile_type_ids_map.get('permeable_wall'),
        'level_ids_map': metatile_level_ids_map
    }

    return prolog_statements, tile_ids_map


def get_config_dimensions(config):
    level_w = config['level_dimensions']['width']
    level_h = config['level_dimensions']['height']
    return level_w, level_h


def get_reachability_constraint(config, constraint, default=False):
    if config.get(constraint) is not None:
        return eval(config[constraint])
    else:
        return default


def setup_tile_position_range(min_index, max_index, level_max):
    if min_index is not None and not (0 <= min_index <= level_max):
        utils.error_exit("invalid min index (%d) given, min index must be in range [0,%d)" % (min_index, level_max))
    if max_index is not None and not (0 <= max_index <= level_max):
        utils.error_exit("invalid max index (%d) given, max index must be in range [0,%d)" % (max_index, level_max))
    if min_index is not None and max_index is not None and min_index > max_index:
        utils.error_exit("min index (%d) cannot exceed max index (%d)" % (min_index, max_index))
    min_index = 0 if min_index is None else min_index
    max_index = level_max - 1 if max_index is None else max_index
    return min_index, max_index


def setup_tile_freq_range(tile_type, min_tiles, max_tiles, lowest, highest):
    if min_tiles is not None and not (lowest <= min_tiles <= highest):
        utils.error_exit("Specified min freq (%d) for '%s' tiles must be in range [%d,%d]" % (min_tiles, tile_type, lowest, highest))
    if max_tiles is not None and not (lowest <= max_tiles <= highest):
        utils.error_exit("Specified max freq (%d) for '%s' tiles be in range [%d,%d]" % (max_tiles, tile_type, lowest, highest))
    if min_tiles is not None and max_tiles is not None and min_tiles > max_tiles:
        utils.error_exit("Specified min freq (%d) for '%s' tiles must be <= max freq (%d)" % (min_tiles, tile_type, max_tiles))
    min_tiles = lowest if min_tiles is None else min_tiles
    max_tiles = highest if max_tiles is None else max_tiles
    return min_tiles, max_tiles


def check_target_type_exists_in_training_level(tile_type, tile_ids_map):
    if tile_ids_map.get('%s_tile_ids' % tile_type) is None or len(tile_ids_map.get('%s_tile_ids' % tile_type)) < 1:
        utils.error_exit("Tile type [%s] does not exist in training level. "
                         "Cannot specify num target count for this type." % tile_type)
    return True


def specific_prolog_statements(config, tile_ids_map):

    prolog_statements = ""

    # ----- GET LEVEL DIMENSIONS -----
    level_w, level_h = get_config_dimensions(config)
    num_tiles = int(level_w * level_h)
    prolog_statements += "dim_width(0..%d).\n" % (level_w - 1)
    prolog_statements += "dim_height(0..%d).\n" % (level_h - 1)
    prolog_statements += "tile(TX,TY) :- dim_width(TX), dim_height(TY).\n"

    # ----- CREATE NON-EMPTY TILE FACTS -----
    non_empty_tile_ids = []
    for tile_type, tile_ids in tile_ids_map.items():
        if 'tile_ids' in tile_type:
            non_empty_tile_ids += tile_ids

    prolog_statements += "non_empty_tile(X,Y) :- tile(X,Y), assignment(X,Y,ID), ID==(%s).\n" % \
                         (';'.join(non_empty_tile_ids))

    # ----- CREATE TILE ID AND STATE VARIABLES -----
    generic_state = State.generic_prolog_contents()

    level_has_wall_tiles = len(tile_ids_map.get('wall_tile_ids')) > 0
    level_has_permeable_wall_tiles = len(tile_ids_map.get('permeable_wall_tile_ids')) > 0
    level_has_bonus_tiles = len(tile_ids_map.get('bonus_tile_ids')) > 0

    wall_tile_id = tile_ids_map.get('wall_tile_ids')[0] if level_has_wall_tiles else None
    permeable_wall_tile_ids = tile_ids_map.get('permeable_wall_tile_ids')
    hazard_tile_ids = tile_ids_map.get('hazard_tile_ids')
    start_tile_id = tile_ids_map.get('start_tile_ids')[0]
    goal_tile_id = tile_ids_map.get('goal_tile_ids')[0]
    block_tile_id = tile_ids_map.get('block_tile_ids')[0]
    bonus_tile_id = tile_ids_map.get('bonus_tile_ids')[0] if level_has_bonus_tiles else None

    # ----- ADD BORDER TILE RULES -----
    if level_has_wall_tiles:
        # Top and bottom border rows must be wall tiles
        prolog_statements += "assignment(X,Y,%s) :- tile(X,Y), Y==(0).\n" % wall_tile_id
        prolog_statements += "assignment(X,Y,%s) :- tile(X,Y), Y==(%d).\n" % (wall_tile_id, level_h-1)

        # Non-border (interior) tiles cannot be wall tiles
        prolog_statements += ":- assignment(X,Y,ID), tile(X,Y), ID==%s, X>0, X<%d, Y>0, Y<%d.\n" % (
            wall_tile_id, level_w-1, level_h-1
        )

        # Left and right border columns can be permeable wall tiles if they exist
        if level_has_permeable_wall_tiles:
            allowed_wall_tile_ids_str = ["ID != %s" % tile_id for tile_id in permeable_wall_tile_ids + [wall_tile_id]]
            prolog_statements += ":- tile(X,Y), assignment(X,Y,ID), X==(0;%d), Y>0, Y<%d, %s.\n" % (
                level_w-1, level_h-1, ','.join(allowed_wall_tile_ids_str)
            )
            # Non-border (interior) tiles cannot be permeable wall tiles
            prolog_statements += ":- assignment(X,Y,ID), tile(X,Y), ID==(%s), X>0, X<%d, Y>0, Y<%d.\n" % (
                ';'.join(permeable_wall_tile_ids), level_w-1, level_h-1
            )
        else:
            prolog_statements += "assignment(X,Y,%s) :- tile(X,Y), X==(0).\n" % wall_tile_id
            prolog_statements += "assignment(X,Y,%s) :- tile(X,Y), X==(%d).\n" % (wall_tile_id, level_w-1)

    # ----- ADD REACHABILITY RULES -----
    require_reachable_platforms = get_reachability_constraint(config, 'require_all_platforms_reachable')
    require_reachable_bonuses = get_reachability_constraint(config, 'require_all_bonus_tiles_reachable')

    # Non-block and non-goal tiles on top of block tiles must have a reachable ground state in them
    if require_reachable_platforms:
        reachable_platform_ids = ';'.join(tile_ids_map.get('block_tile_ids') + tile_ids_map.get('one_way_platform_tile_ids'))

        tiles_ids_to_ignore = ','.join(["ID1 != %s" % tile_id for tile_id in tile_ids_map.get('goal_tile_ids') +
                                        tile_ids_map.get('block_tile_ids') + tile_ids_map.get('wall_tile_ids')])

        prolog_statements += "tile_above_block(TX,TY) :- tile(TX,TY), assignment(TX,TY,ID1), %s, tile(TX,TY+1), " \
                             "assignment(TX,TY+1,ID2), ID2 == (%s).\n" % (tiles_ids_to_ignore, reachable_platform_ids)

        prolog_statements += "tile_has_reachable_ground_state(TX,TY) :- tile(TX,TY), reachable(%s), %s, TX==X/%d, TY==Y/%d.\n"  % \
                             (generic_state, State.generic_ground_reachability_expression(), TILE_DIM, TILE_DIM)

        prolog_statements += ":- tile_above_block(TX,TY), not tile_has_reachable_ground_state(TX,TY).\n"

    # Bonus tiles must have a reachable bonus state in the tile below them
    if level_has_bonus_tiles and require_reachable_bonuses:
        prolog_statements += "tile_below_bonus(TX,TY) :- tile(TX,TY), tile(TX,TY-1), assignment(TX,TY-1,%s).\n" % bonus_tile_id
        prolog_statements += "tile_has_reachable_bonus_state(TX,TY) :- tile(TX,TY), reachable(%s), %s, TX==X/%d, TY==Y/%d.\n" % \
                             (generic_state, State.generic_bonus_reachability_expression(), TILE_DIM, TILE_DIM)
        prolog_statements += ":- tile_below_bonus(TX,TY), not tile_has_reachable_bonus_state(TX,TY).\n"

    # ----- ADD START/GOAL ON_GROUND RULES -----
    start_on_ground = get_reachability_constraint(config, 'require_start_on_ground')
    goal_on_ground = get_reachability_constraint(config, 'require_goal_on_ground')

    allowed_ground_tile_ids_str = ','.join(["ID != %s" % tile_id for tile_id in tile_ids_map.get('block_tile_ids') +
                                            tile_ids_map.get('one_way_platform_tile_ids')])

    if start_on_ground:
        prolog_statements += ":- tile(X,Y), tile(X,Y+1), assignment(X,Y,%s), assignment(X,Y+1,ID), metatile(ID), " \
                             "%s.\n" % (start_tile_id, allowed_ground_tile_ids_str)

    if goal_on_ground:
        prolog_statements += ":- tile(X,Y), tile(X,Y+1), assignment(X,Y,%s), assignment(X,Y+1,ID), metatile(ID), " \
                             "%s.\n" % (goal_tile_id, allowed_ground_tile_ids_str)

    # ----- SET START/GOAL ALLOWED TILE INDEX POSITION RANGES
    tile_position_ranges = {
        'start_column': (0, level_w - 1),
        'start_row': (0, level_h - 1),
        'goal_column': (0, level_w - 1),
        'goal_row': (0, level_h - 1)
    }

    if config.get('tile_position_ranges') is not None:
        for position, range_str in config['tile_position_ranges'].items():
            if tile_position_ranges.get(position) is None:
                utils.error_exit("%s tile position does not exist. Position must be one of %s" %
                                 (position, str(list(tile_position_ranges.keys()))))
            level_max = level_w if 'column' in position else level_h
            min_index, max_index = eval(range_str)
            min_index, max_index = setup_tile_position_range(min_index, max_index, level_max)
            tile_position_ranges[position] = (min_index, max_index)

    start_tile_min_x, start_tile_max_x = tile_position_ranges.get('start_column')
    start_tile_min_y, start_tile_max_y = tile_position_ranges.get('start_row')
    goal_tile_min_x, goal_tile_max_x = tile_position_ranges.get('goal_column')
    goal_tile_min_y, goal_tile_max_y = tile_position_ranges.get('goal_row')

    prolog_statements += ":- assignment(X,Y,%s), X < %d.\n" % (start_tile_id, start_tile_min_x)
    prolog_statements += ":- assignment(X,Y,%s), X > %d.\n" % (start_tile_id, start_tile_max_x)
    prolog_statements += ":- assignment(X,Y,%s), Y < %d.\n" % (start_tile_id, start_tile_min_y)
    prolog_statements += ":- assignment(X,Y,%s), Y > %d.\n" % (start_tile_id, start_tile_max_y)

    prolog_statements += ":- assignment(X,Y,%s), X < %d.\n" % (goal_tile_id, goal_tile_min_x)
    prolog_statements += ":- assignment(X,Y,%s), X > %d.\n" % (goal_tile_id, goal_tile_max_x)
    prolog_statements += ":- assignment(X,Y,%s), Y < %d.\n" % (goal_tile_id, goal_tile_min_y)
    prolog_statements += ":- assignment(X,Y,%s), Y > %d.\n" % (goal_tile_id, goal_tile_max_y)

    # ----- SPECIFY TARGET NUM TILES FOR A GIVEN TYPE -----
    target_num_tiles = {}
    if config.get('target_num_tiles') is not None:
        for tile_type, target_str in config['target_num_tiles'].items():
            target = eval(target_str)
            if target is not None:
                check_target_type_exists_in_training_level(tile_type, tile_ids_map)
                target_num_tiles[tile_type] = target

    if len(target_num_tiles) > 0:
        priority = len(target_num_tiles)
        for tile_type, target_count in target_num_tiles.items():

            target_leeway = int(target_count * 0.20)  # stay within 20% range of target count

            if tile_type == 'hazard':
                prolog_statements += "hazard_count(C) :- C = #count { X,Y : assignment(X,Y,MT), MT==(%s) }.\n" % hazard_tile_ids
                prolog_statements += "hazard_penalty(P) :- P = #max { 0; |%d-C|-%d : hazard_count(C) }.\n" % (target_count, target_leeway)
                prolog_statements += "#minimize { P@%d, P : hazard_penalty(P) }.\n" % priority

            if tile_type == 'block':
                prolog_statements += "block_count(C) :- C = #count { X,Y : assignment(X,Y,MT), MT==(%s) }.\n" % block_tile_id
                prolog_statements += "block_penalty(P) :- P = #max { 0; |%d-C|-%d : block_count(C) }.\n" % (target_count, target_leeway)
                prolog_statements += "#minimize { P@%d, P : block_penalty(P) }.\n" % priority

            if tile_type == 'bonus':
                prolog_statements += "bonus_count(C) :- C = #count { X,Y : assignment(X,Y,MT), MT==(%s) }.\n" % bonus_tile_id
                prolog_statements += "bonus_penalty(P) :- P = #max { 0; |%d-C|-%d : bonus_count(C) }.\n" % (target_count, target_leeway)
                prolog_statements += "#minimize { P@%d, P : bonus_penalty(P) }.\n" % priority

            priority -= 1

    # ----- SPECIFY NUM TILE RANGES FOR A GIVEN TYPE
    num_tile_ranges = {}
    lo, hi = 0, num_tiles
    if config.get('num_tile_ranges') is not None:
        for tile_type, range_str in config.get('num_tile_ranges').items():
            check_target_type_exists_in_training_level(tile_type, tile_ids_map)
            min_tiles, max_tiles = eval(range_str)
            num_tile_ranges[tile_type] = setup_tile_freq_range(tile_type, min_tiles, max_tiles, lo, hi)

    for tile_type, tile_range in num_tile_ranges.items():
        if tile_type == 'empty':
            min_empty, max_empty = tile_range
            min_non_empty, max_non_empty = num_tiles - max_empty, num_tiles - min_empty
            prolog_statements += "%d { non_empty_tile(X,Y) : tile(X,Y) } %d.\n" % \
                                 (min_non_empty, max_non_empty)
        elif tile_type == 'one_way_platform':
            utils.error_exit("enforcing one_way_platform num_tile_ranges is not supported yet")
            # tmp_prolog_statements += "%d { one_way_tile(X,Y) : tile(X,Y) } %d.\n" % (
            #     tile_range[0], tile_range[1])
        else:
            tile_ids = tile_ids_map.get('%s_tile_ids' % tile_type)
            if len(tile_ids) > 0:
                prolog_statements += "limit(%s,%d,%d).\n" % (tile_ids[0], tile_range[0], tile_range[1])

    return prolog_statements


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


def get_tile_char(tile_id, tile_ids_map):
    for tile_type, tile_ids in tile_ids_map.items():
        if tile_id in tile_ids:
            return list(TILE_CHARS[tile_type.split('_tile_ids')[0]].keys())[0]
    return list(TILE_CHARS['empty'].keys())[0]  # empty


def convert_assignments_dict_into_level(assignments_dict, level_w, level_h, tile_ids_map):
    level_structural_txt = ""
    for row in range(level_h):
        for col in range(level_w):
            tile_xy = (col, row)
            tile_id = assignments_dict.get(tile_xy)
            tile_char = get_tile_char(tile_id, tile_ids_map)
            level_structural_txt += tile_char
        level_structural_txt += "\n"
    return level_structural_txt


def main(tile_constraints_file, config_file, max_sol, threads, print_level, save, validate):
    level_saved_files_dir, prolog_filename = parse_constraints_filepath(tile_constraints_file)
    prolog_filepath = utils.get_filepath("%s/prolog_files" % level_saved_files_dir, "%s.pl" % prolog_filename)

    general_prolog, tile_ids_map = general_prolog_statements(tile_constraints_file)
    config_file_contents = utils.read_json(config_file)
    config = config_file_contents['config']
    specific_prolog = specific_prolog_statements(config, tile_ids_map)
    utils.write_file(prolog_filepath, general_prolog + specific_prolog)

    answer_set_prefix = '_'.join([prolog_filename] + '_'.join(config_file.split('/')[1:]).split('.json')[:1])
    level_w, level_h = get_config_dimensions(config)

    with open("%s/%s.txt" % (GENERATED_MODEL_STRS_DIR, answer_set_prefix), 'wb') as f:
        clingo_cmd = "clingo %s --models %d --sign-def rnd --time-limit 1800" % (prolog_filepath, max_sol)
        process = subprocess.Popen(clingo_cmd.split(' '), stdout=subprocess.PIPE)

        generated_sol_idx = 0
        # while os.path.exists("%s/%s_a%d.txt" % (GENERATED_LEVELS_DIR, answer_set_prefix, generated_sol_idx)):
        #     generated_sol_idx += 1

        model_str = None

        for line in iter(lambda: process.stdout.readline(), b''):
            decoded_line = line.decode('utf-8')
            sys.stdout.write(decoded_line)
            f.write(line)

            if b'Answer:' in line and model_str is None:
                model_str = ""  # start new model_str

            elif (b'Answer:' in line or b'Models' in line) and model_str is not None and save:
                assignments_dict = create_assignments_dict(model_str)  # parse previous model_str and start new one
                generated_level_txt = convert_assignments_dict_into_level(assignments_dict, level_w, level_h, tile_ids_map)

                level_txt_outfile = utils.get_filepath(GENERATED_LEVELS_DIR, "%s_a%d.txt" % (
                    answer_set_prefix, generated_sol_idx))
                utils.write_file(level_txt_outfile, generated_level_txt)

                assignments_dict_outfile = utils.get_filepath(GENERATED_ASSIGNMENTS_DICTS_DIR, "%s_a%d.txt" % (
                    answer_set_prefix, generated_sol_idx))
                utils.write_file(assignments_dict_outfile, str(assignments_dict))

                model_str = ""
                generated_sol_idx += 1

            elif model_str is not None:
                model_str += decoded_line + "\n"

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run solver and create new levels from valid answer sets')
    parser.add_argument('tile_constraints_file', type=str, help='File path of the metatile constraints file for the training level')
    parser.add_argument('config_file', type=str, help="File path of the json file to use to specify design decisions")
    parser.add_argument('--max_sol', type=int, default=1, help="Max number of answer sets to return")
    parser.add_argument('--threads', type=int, default=1, help="Number of threads to run the solver on")
    parser.add_argument('--print_level', const=True, nargs='?', type=bool, default=False, help="Print structural txt layer of generated levels")
    parser.add_argument('--save', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--validate', const=True, nargs='?', type=bool, default=False, help="Validate generated levels")
    args = parser.parse_args()

    main(tile_constraints_file=args.tile_constraints_file,
         config_file=args.config_file, max_sol=args.max_sol, threads=args.threads,
         print_level=args.print_level, save=args.save, validate=args.validate)
