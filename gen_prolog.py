import networkx as nx
import re
import os
import argparse

from model.metatile import METATILE_TYPES
from stopwatch import Stopwatch
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
    return level_saved_files_dir, prolog_filename


def main(tile_constraints_file, debug, print_pl, save):

    stopwatch = Stopwatch()

    print("Generating prolog file for constraints file: %s ..." % tile_constraints_file)
    stopwatch.start()

    # Setup save file directory and get save filepath
    level_saved_files_dir, prolog_filename = parse_constraints_filepath(tile_constraints_file)
    prolog_filepath = utils.get_filepath("%s/prolog_files" % level_saved_files_dir, "%s.pl" % prolog_filename)

    # Load in tile_id constraints
    tile_id_constraints_dict = utils.read_pickle(tile_constraints_file)

    # Create prolog statements
    prolog_statements = ""
    prolog_statements += "dim_metatiles(1..%d).\n" % len(tile_id_constraints_dict)

    # Limit num metatile assignments per tile
    min_assignments = 0 if debug else 1
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
            prolog_statements += "linkout(%s,%s) :- assignment(TX,TY,%s), tile(TX,TY).\n" % (src_state_contents, dest_state_contents, tile_id)
            prolog_statements += "linkin(%s,%s) :- assignment(TX,TY,%s), tile(TX,TY).\n" % (src_state_contents, dest_state_contents, tile_id)

    # Add rule for valid links
    prolog_statements += ":- linkout(%s,%s), state(%s), not state(%s).\n" % (generic_src_state, generic_dest_state, generic_src_state, generic_dest_state)
    prolog_statements += ":- linkout(%s,%s), not linkin(%s,%s), state(%s).\n" % (generic_src_state, generic_dest_state, generic_src_state, generic_dest_state, generic_src_state)
    prolog_statements += ":- linkin(%s,%s), state(%s), not state(%s).\n" % (generic_dest_state, generic_src_state, generic_src_state, generic_dest_state)
    prolog_statements += ":- linkin(%s,%s), not linkout(%s,%s), state(%s).\n" % (generic_dest_state, generic_src_state, generic_dest_state, generic_src_state, generic_src_state)

    # Create legal adjacency prolog facts: legal(dx, dy, tile_id, neighbor_wfc_type)
    for tile_id, adjacency_dict in tile_id_adjacent_types_map.items():
        for direction, neighbor_wfc_types in adjacency_dict.items():
            for neighbor_wfc_type in neighbor_wfc_types:
                prolog_statements += "legal(%s,%s,%s,%s).\n" % (direction[0], direction[1], tile_id, neighbor_wfc_type)

    # Get block, start, and goal tile_ids
    block_tile_id = metatile_type_ids_map.get("block")[0]
    start_tile_id = metatile_type_ids_map.get("start")[0]
    goal_tile_id = metatile_type_ids_map.get("goal")[0]
    hazard_tile_ids = metatile_type_ids_map.get("hazard")
    wall_tile_ids = metatile_type_ids_map.get("wall")
    permeable_wall_tile_ids = metatile_type_ids_map.get("permeable_wall")

    # Get bonus tile id if exists
    bonus_tile_ids = metatile_type_ids_map.get("bonus")
    bonus_tile_id = None if len(bonus_tile_ids) == 0 else bonus_tile_ids[0]

    # Limit number of tiles of specified tile_id
    limit_tile_id_rule = "MIN { assignment(X,Y,MT) : metatile(MT), tile(X,Y) } MAX :- limit(MT, MIN, MAX)."
    prolog_statements += limit_tile_id_rule + "\n"
    prolog_statements += "limit(%s, 1, 1).\n" % start_tile_id
    prolog_statements += "limit(%s, 1, 1).\n" % goal_tile_id

    # Add state reachable rule
    state_reachable_rule = "reachable(%s) :- linkin(%s,%s), linkout(%s,%s), state(%s), state(%s), reachable(%s)." % (
        generic_dest_state, generic_src_state, generic_dest_state, generic_src_state, generic_dest_state,
        generic_src_state, generic_dest_state, generic_src_state
    )
    prolog_statements += state_reachable_rule + "\n"

    # Start states are inherently reachable
    prolog_statements += "reachable(%s) :- state(%s), %s.\n" % (generic_state, generic_state, State.generic_start_reachability_expression())

    # Goal states must be reachable
    prolog_statements += ":- state(%s), not reachable(%s), %s.\n" % (generic_state, generic_state, State.generic_goal_reachability_expression())

    # Get one_way_platform tile_ids
    one_way_platform_tile_ids = metatile_type_ids_map.get("one_way_platform")

    # ASP WFC algorithm rule
    wfc_rule = ":- adj(X1,Y1,X2,Y2,DX,DY), assignment(X1,Y1,MT1), assignment(X2,Y2,MT2), wfc(T1,MT1), wfc(T2,MT2), not legal(DX,DY,MT1,T2)."
    prolog_statements += wfc_rule + "\n"

    # Remove duplicate prolog statements
    prolog_statements = utils.get_unique_lines(prolog_statements)

    # Print
    if print_pl:
        print(prolog_statements)

    # Update all_prolog_info file
    all_prolog_info_filepath = utils.get_filepath("%s/prolog_files" % level_saved_files_dir,
                                                  "all_prolog_info.pickle")
    all_prolog_info_map = utils.read_pickle(all_prolog_info_filepath) if os.path.exists(
        all_prolog_info_filepath) else {}

    all_prolog_info_map[prolog_filename] = {
        "block_tile_ids": [block_tile_id],
        "start_tile_ids": [start_tile_id],
        "goal_tile_ids": [goal_tile_id],
        "bonus_tile_ids": [] if bonus_tile_id is None else [bonus_tile_id],
        "one_way_platform_tile_ids": one_way_platform_tile_ids,
        "hazard_tile_ids": hazard_tile_ids,
        "wall_tile_ids": wall_tile_ids,
        "permeable_wall_tile_ids": permeable_wall_tile_ids,
        "level_ids_map": metatile_level_ids_map
    }

    if save:
        utils.write_file(prolog_filepath, prolog_statements)
        utils.write_pickle(all_prolog_info_filepath, all_prolog_info_map)

    runtime = stopwatch.stop()

    return prolog_filepath, runtime


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate prolog file')
    parser.add_argument('tile_constraints_file', type=str, help="File path of the tile constraints dictionary to use")
    parser.add_argument('--debug', const=True, nargs='?', type=bool, default=False, help='Allow empty tiles if no suitable assignment can be found')
    parser.add_argument('--print_pl', const=True, nargs='?', type=bool, default=False, help='Print prolog statements to console')
    parser.add_argument('--save', const=True, nargs='?', type=bool, default=False, help='Save generated prolog file')
    args = parser.parse_args()

    main(args.tile_constraints_file, args.debug, args.print_pl, args.save)
