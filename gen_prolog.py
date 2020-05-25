import networkx as nx
import re
import os
import argparse
from datetime import datetime

from model.level import TILE_DIM
from model.metatile import METATILE_TYPES
import utils

# Acknowledgements and References:
# - Legal adjacency rules based on NPCDev groundcollapse
# - WFC in ASP implementation: based on Karth, I., & Smith, A. M. (2017). WaveFunctionCollapse is constraint solving
#   in the wild. Proceedings of the 12th International Conference on the Foundations of Digital Games, 68. ACM.


if os.getenv('MAZE'):
    print('***** USING MAZE RULES *****')
    from model_maze.state import StateMaze as State

else:
    print('***** USING PLATFORMER RULES *****')
    from model_platformer.state import StatePlatformer as State


def parse_constraints_filepath(constraints_filename):
    match = re.match(r'([^/]+)/metatile_constraints/([a-zA-Z0-9_-]+).pickle', constraints_filename)
    level_saved_files_dir = match.group(1)
    prolog_filename = match.group(2)
    return level_saved_files_dir + "/", prolog_filename


def main(tile_constraints_file, debug, print_pl):

    print("Generating prolog file for constraints file: %s ..." % tile_constraints_file)
    start_time = datetime.now()

    # Set up save file directory
    level_saved_files_dir, prolog_filename = parse_constraints_filepath(tile_constraints_file)
    prolog_filepath = utils.get_filepath(level_saved_files_dir + "prolog_files", "%s.pl" % prolog_filename)

    # Load in tile constraints dictionary
    tile_id_constraints_dict = utils.read_pickle(tile_constraints_file)

    # Generate prolog statements
    prolog_statements = ""
    prolog_statements += "dim_metatiles(1..%d).\n" % (len(tile_id_constraints_dict.keys()))

    # Limit number of metatile assignments per tile
    min_assignments = 0 if debug else 1
    limit_metatile_per_tile_rule = "%d {assignment(TX, TY, MT) : metatile(MT) } 1 :- tile(TX,TY)." % min_assignments
    prolog_statements += limit_metatile_per_tile_rule + "\n"

    # Create tile adjacency rules
    adj_rule_prefix = "adj(X1,Y1,X2,Y2,DX,DY) :- tile(X1,Y1), tile(X2,Y2), X2-X1 == DX, Y2-Y1 == DY"
    horizontal_adj_rule = "%s, |DX| == 1, DY == 0." % adj_rule_prefix
    vertical_adj_rule = "%s, DX == 0, |DY| == 1." % adj_rule_prefix
    diagonal_adj_rule = "%s, |DX| == 1, |DY| == 1." % adj_rule_prefix
    prolog_statements += horizontal_adj_rule + "\n"
    prolog_statements += vertical_adj_rule + "\n"
    prolog_statements += diagonal_adj_rule + "\n"

    metatile_type_ids_map = {}
    for type in METATILE_TYPES:
        metatile_type_ids_map[type] = []  # {metatile_type: list-metatile-ids}

    metatile_level_ids_map = {}

    start_state = None
    goal_state = None

    # Create metatile facts, metatile_type facts, and legal neighbor statements for the specified tile constraints dict

    for tile_id, tile_constraints in tile_id_constraints_dict.items():

        metatile_fact = "metatile(%s)." % tile_id
        prolog_statements += metatile_fact + "\n"

        metatile_type = tile_constraints.get('type')
        metatile_type_ids_map[metatile_type].append(tile_id)

        metatile_levels = tile_constraints.get('levels')
        for level in metatile_levels:
            if metatile_level_ids_map.get(level) is None:
                metatile_level_ids_map[level] = [tile_id]
            else:
                metatile_level_ids_map[level].append(tile_id)

        metatile_graph = nx.DiGraph(tile_constraints.get('graph'))

        # Create state and link rules based on metatile graph

        for edge in metatile_graph.edges():
            src_state = State.from_str(edge[0])
            dest_state = State.from_str(edge[1])
            src_state_contents = src_state.to_prolog_contents()
            dest_state_contents = dest_state.to_prolog_contents()

            state_rule = "state(%s) :- assignment(TX,TY,%s)." % (src_state_contents, tile_id)
            link_rule = "link(%s,%s) :- assignment(TX,TY,%s)." % (src_state_contents, dest_state_contents, tile_id)
            prolog_statements += state_rule + "\n"
            prolog_statements += link_rule + "\n"

            # Define start fact in prolog
            if start_state is None and src_state.is_start:
                start_rule = "start(%s) :- assignment(TX,TY,%s)." % (src_state_contents, tile_id)
                prolog_statements += start_rule + "\n"
                start_state = src_state

            # Define goal fact in prolog
            if goal_state is None and src_state.goal_reached:
                goal_rule = "goal(%s) :- assignment(TX,TY,%s)." % (dest_state_contents, tile_id)
                prolog_statements += goal_rule + "\n"
                goal_state = src_state

        # Create legal rules based on valid adjacent tiles
        for direction, adjacent_tiles in tile_constraints.get("adjacent").items():  # for each adjacent dir
            dx, dy = direction

            for adjacent_id in adjacent_tiles:  # for each adjacent metatile
                legal_statement = "legal(DX, DY, MT1, MT2) :- DX == %d, DY == %d, metatile(MT1), metatile(MT2), " \
                                  "MT1 == %s, MT2 == %s." % (dx, dy, tile_id, adjacent_id)
                prolog_statements += legal_statement + "\n"

    generic_state = State.generic_prolog_contents()
    generic_src_state = State.generic_prolog_contents(index=1)
    generic_dest_state = State.generic_prolog_contents(index=2)

    link_exists_rule = ":- link(%s,%s), state(%s), not state(%s)." % (generic_src_state, generic_dest_state,
                                                                      generic_src_state, generic_dest_state)
    prolog_statements += link_exists_rule

    # Get block, start, and goal tile_ids
    block_tile_id = metatile_type_ids_map.get("block")[0]
    start_tile_id = metatile_type_ids_map.get("start")[0]
    goal_tile_id = metatile_type_ids_map.get("goal")[0]
    hazard_tile_ids = metatile_type_ids_map.get("hazard")
    wall_tile_ids = metatile_type_ids_map.get("wall")

    # Get bonus tile id if exists
    bonus_tile_ids = metatile_type_ids_map.get("bonus")
    bonus_tile_id = None if len(bonus_tile_ids) == 0 else bonus_tile_ids[0]

    # Limit number of tiles of specified tile id
    limit_tile_type_rule = "MIN { assignment(X,Y,MT) : metatile(MT), tile(X,Y) } MAX :- limit(MT, MIN, MAX)."
    prolog_statements += limit_tile_type_rule + "\n"

    # Limit number of goal tiles
    prolog_statements += "limit(%s, 1, 1).\n" % goal_tile_id

    # Limit number of start tiles
    prolog_statements += "limit(%s, 1, 1).\n" % start_tile_id

    # Start state is inherently reachable
    start_reachable_rule = "reachable(%s) :- start(%s)." % (generic_state, generic_state)
    prolog_statements += start_reachable_rule + "\n"

    # Goal state must be reachable
    goal_reachable_rule = ":- goal(%s), not reachable(%s)." % (generic_state, generic_state)
    prolog_statements += goal_reachable_rule + "\n"

    # State reachable rule
    state_reachable_rule = "reachable(%s) :- link(%s,%s), state(%s), state(%s), reachable(%s)." % (generic_dest_state,
                                                                                                   generic_src_state, generic_dest_state,
                                                                                                   generic_src_state, generic_dest_state,
                                                                                                   generic_src_state)
    prolog_statements += state_reachable_rule + "\n"

    # Tile reachable rule (only if state in top half of the tile is reachable)
    reachable_tile_rule = "reachable_tile(X/T,Y/T) :- reachable(%s), Y\\T <= T/2, T=%d." % (generic_state, TILE_DIM)
    prolog_statements += reachable_tile_rule + "\n"

    # Ensure that bonus tiles can be collected
    if bonus_tile_id is not None:
        bonus_reachable_rule = ":- assignment(TX,TY,%s), not reachable_tile(TX,TY+1)." % bonus_tile_id
        prolog_statements += bonus_reachable_rule + "\n"

    # Ensure that tiles above platforms are reachable if they are not block/bonus/goal tiles
    exception_tile_ids = [block_tile_id, goal_tile_id]
    exception_tile_ids += [] if bonus_tile_id is None else [bonus_tile_id]
    exception_tile_assignments = ["not assignment(X,Y-1,%s)" % tile_id for tile_id in exception_tile_ids]
    platform_reachable_rule = ":- assignment(X,Y,%s), not reachable_tile(X,Y-1), %s." % (block_tile_id, ', '.join(exception_tile_assignments))
    prolog_statements += platform_reachable_rule + "\n"

    # Add one-way platform tile prolog rules
    one_way_platform_tile_ids = metatile_type_ids_map.get("one_way_platform")

    if len(one_way_platform_tile_ids) > 0:
        # Disallow vertically stacking one-way platform tiles
        for tile_id_bottom in one_way_platform_tile_ids:
            for tile_id_top in one_way_platform_tile_ids:
                prolog_statements += ":- assignment(X,Y,%s), assignment(X,Y-1,%s).\n" % (tile_id_bottom, tile_id_top)

        # Ensure that tiles above one-way platform tiles are reachable
        for tile_id in one_way_platform_tile_ids:
            one_way_platform_reachable_rule = ":- assignment(X,Y,%s), not reachable_tile(X,Y-1)." % tile_id
            prolog_statements += one_way_platform_reachable_rule + "\n"

    # ASP WFC algorithm rule
    wfc_rule = ":- adj(X1,Y1,X2,Y2,DX,DY), assignment(X1,Y1,MT1), not 1 { assignment(X2,Y2,MT2) : legal(DX,DY,MT1,MT2) }."
    prolog_statements += wfc_rule + "\n"

    # Remove duplicate statements
    prolog_statements = utils.get_unique_lines(prolog_statements)

    # Print
    if print_pl:
        print(prolog_statements)

    # Save prolog file
    utils.write_file(prolog_filepath, prolog_statements)

    # Update all_prolog_info file
    all_prolog_info_filepath = utils.get_filepath(level_saved_files_dir + "prolog_files", "all_prolog_info.pickle")
    all_prolog_info_map = utils.read_pickle(all_prolog_info_filepath) if os.path.exists(all_prolog_info_filepath) else {}

    if all_prolog_info_map.get(prolog_filename) is not None:
        del all_prolog_info_map[prolog_filename]  # remove the old prolog info for the given tile constraints

    all_prolog_info_map[prolog_filename] = {
        "block_tile_ids": [block_tile_id],
        "start_tile_ids": [start_tile_id],
        "goal_tile_ids": [goal_tile_id],
        "bonus_tile_ids": [] if bonus_tile_id is None else [bonus_tile_id],
        "one_way_platform_tile_ids": one_way_platform_tile_ids,
        "hazard_tile_ids": hazard_tile_ids,
        "wall_tile_ids": wall_tile_ids,
        "level_ids_map": metatile_level_ids_map
    }

    utils.write_pickle(all_prolog_info_filepath, all_prolog_info_map)

    end_time = datetime.now()
    runtime = str(end_time-start_time)
    print("Runtime: %s\n" % runtime)

    return prolog_filepath, runtime


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate prolog file')
    parser.add_argument('tile_constraints_file', type=str, help="File path of the tile constraints dictionary to use")
    parser.add_argument('--debug', const=True, nargs='?', type=bool, default=False, help='Allow empty tiles if no suitable assignment can be found')
    parser.add_argument('--print_pl', const=True, nargs='?', type=bool, default=False, help='Print prolog statements to console')
    args = parser.parse_args()

    main(args.tile_constraints_file, args.debug, args.print_pl)
