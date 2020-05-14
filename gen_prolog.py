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

    # Enforce symmetric legal adjacencies
    symmetric_legal_adjacencies_rule = "legal(DX, DY, P1, P2) :- legal(IDX, IDY, P2, P1), IDX == -DX, IDY == -DY."
    prolog_statements += symmetric_legal_adjacencies_rule + "\n"

    metatile_type_ids_map = {}
    for type in METATILE_TYPES:
        metatile_type_ids_map[type] = []  # {metatile_type: list-metatile-ids}
    start_state = None
    goal_state = None

    # Create metatile facts, metatile_type facts, and legal neighbor statements for the specified tile constraints dict

    for tile_id, tile_constraints in tile_id_constraints_dict.items():

        metatile_fact = "metatile(%s)." % tile_id
        prolog_statements += metatile_fact + "\n"

        metatile_type = tile_constraints.get('type')
        metatile_type_ids_map[metatile_type].append(tile_id)

        metatile_graph = nx.DiGraph(tile_constraints.get('graph'))

        # Create state and link rules based on metatile graph

        for edge in metatile_graph.edges():
            src_state = eval(edge[0])
            dest_state = eval(edge[1])
            src_x, src_y, dest_x, dest_y = src_state['x'], src_state['y'], dest_state['x'], dest_state['y']

            state_rule = "state(%d+TX*%d, %d+TY*%d) :- assignment(TX,TY,%s)." % (src_x, TILE_DIM, src_y, TILE_DIM, tile_id)
            link_rule = "link(%d+TX*%d, %d+TY*%d, %d+TX*%d, %d+TY*%d) :- assignment(TX,TY,%s)." % \
                        (src_x, TILE_DIM, src_y, TILE_DIM, dest_x, TILE_DIM, dest_y, TILE_DIM, tile_id)
            prolog_statements += state_rule + "\n"
            prolog_statements += link_rule + "\n"

            # Define start fact in prolog
            if start_state is None and src_state['is_start']:
                start_rule = "start(%d+TX*%d, %d+TY*%d) :- assignment(TX,TY,%s)." % (src_x, TILE_DIM, src_y, TILE_DIM, tile_id)
                prolog_statements += start_rule + "\n"
                start_state = src_state

            # Define goal fact in prolog
            if goal_state is None and src_state['goal_reached']:
                goal_rule = "goal(%d+TX*%d, %d+TY*%d) :- assignment(TX,TY,%s)." % (src_x, TILE_DIM, src_y, TILE_DIM, tile_id)
                prolog_statements += goal_rule + "\n"
                goal_state = src_state

        # Create legal rules based on valid adjacent tiles
        for direction, adjacent_tiles in tile_constraints.get("adjacent").items():  # for each adjacent dir
            dx, dy = direction

            for adjacent_id in adjacent_tiles:  # for each adjacent metatile
                legal_statement = "legal(DX, DY, MT1, MT2) :- DX == %d, DY == %d, metatile(MT1), metatile(MT2), " \
                                  "MT1 == %s, MT2 == %s." % (dx, dy, tile_id, adjacent_id)
                prolog_statements += legal_statement + "\n"

    # Link can only exist if the src and dest states exist, otherwise solution is not valid
    link_exists_rule = ":- link(X1,Y1,X2,Y2), state(X1,Y1), not state(X2,Y2)."
    prolog_statements += link_exists_rule

    # Get block, start, and goal tile_ids
    block_tile_id = metatile_type_ids_map.get("block")[0]
    start_tile_id = metatile_type_ids_map.get("start")[0]
    goal_tile_id = metatile_type_ids_map.get("goal")[0]

    # Get bonus tile id if exists
    bonus_tile_ids = metatile_type_ids_map.get("bonus")
    bonus_tile_id = None if len(bonus_tile_ids) == 0 else bonus_tile_ids[0]

    # Start state is inherently reachable
    start_reachable_rule = "reachable(X,Y) :- start(X,Y)."
    prolog_statements += start_reachable_rule + "\n"

    # Goal state must be reachable
    goal_reachable_rule = ":- goal(X,Y), not reachable(X,Y)."
    prolog_statements += goal_reachable_rule + "\n"

    # State reachable rule
    state_reachable_rule = "reachable(X2,Y2) :- link(X1,Y1,X2,Y2), state(X1,Y2), state(X2,Y2), reachable(X1,Y1)."
    prolog_statements += state_reachable_rule + "\n"

    # Tile reachable rule (only if state in top half of the tile is reachable)
    reachable_tile_rule = "reachable_tile(X/%d,Y/%d) :- reachable(X,Y), Y\\%d <= %d/2." % (TILE_DIM, TILE_DIM, TILE_DIM, TILE_DIM)
    prolog_statements += reachable_tile_rule + "\n"

    # Ensure that bonus tiles can be collected
    if bonus_tile_id is not None:
        bonus_reachable_rule = ":- assignment(TX,TY,%s), not reachable_tile(TX,TY+1)." % bonus_tile_id
        prolog_statements += bonus_reachable_rule + "\n"

    # Start on ground rule (start tile must be on top of a block tile)
    start_on_ground_rule = ":- assignment(X,Y,%s), not assignment(X,Y+1,%s)." % (start_tile_id, block_tile_id)
    prolog_statements += start_on_ground_rule + "\n"

    # Goal on ground rule (goal tile must be on top of a block tile)
    goal_on_ground_rule = ":- assignment(X,Y,%s), not assignment(X,Y+1,%s)." % (goal_tile_id, block_tile_id)
    prolog_statements += goal_on_ground_rule + "\n"

    # # Ensure that tiles above platforms are reachable if they are not block/bonus/goal tiles
    exception_tile_ids = [block_tile_id, goal_tile_id]
    exception_tile_ids += [] if bonus_tile_id is None else [bonus_tile_id]
    exception_tile_assignments = ["not assignment(X,Y-1,%s)" % tile_id for tile_id in exception_tile_ids]
    platform_reachable_rule = ":- assignment(X,Y,%s), not reachable_tile(X,Y-1), %s." % (block_tile_id, ', '.join(exception_tile_assignments))
    prolog_statements += platform_reachable_rule + "\n"

    # Add one-way platform tile prolog rules
    one_way_platform_tile_ids = metatile_type_ids_map.get("one_way_platform")
    one_way_platform_tile_ids = None if len(one_way_platform_tile_ids) == 0 else one_way_platform_tile_ids

    if one_way_platform_tile_ids is not None:

        # Disallow vertically stacking one-way platform tiles
        for tile_id_bottom in one_way_platform_tile_ids:
            for tile_id_top in one_way_platform_tile_ids:
                prolog_statements += ":- assignment(X,Y,%s), assignment(X,Y-1,%s).\n" % (tile_id_bottom, tile_id_top)

        # Ensure that tiles above one-way platform tiles are reachable
        for tile_id in one_way_platform_tile_ids:
            one_way_platform_reachable_rule = ":- assignment(X,Y,%s), not reachable_tile(X,Y-1)." % tile_id
            prolog_statements += one_way_platform_reachable_rule + "\n"

    # Limit number of tiles of specified tile id
    limit_tile_type_rule = "MIN { assignment(X,Y,MT) : metatile(MT), tile(X,Y) } MAX :- limit(MT, MIN, MAX)."
    prolog_statements += limit_tile_type_rule + "\n"

    # Limit number of goal tiles
    prolog_statements += "limit(%s, 1, 1).\n" % goal_tile_id

    # Limit number of start tiles
    prolog_statements += "limit(%s, 1, 1).\n" % start_tile_id

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
        "filepath": prolog_filepath,
        "block_tile_id": block_tile_id,
        "start_tile_id": start_tile_id,
        "goal_tile_id": goal_tile_id,
        "bonus_tile_id": bonus_tile_id,
        "one_way_tile_ids": one_way_platform_tile_ids
    }

    utils.write_pickle(all_prolog_info_filepath, all_prolog_info_map)

    end_time = datetime.now()
    print("Runtime: %s" % str(end_time-start_time))

    return prolog_filepath


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate prolog file')
    parser.add_argument('tile_constraints_file', type=str, help="File path of the tile constraints dictionary to use")
    parser.add_argument('--debug', const=True, nargs='?', type=bool, default=False, help='Allow empty tiles if no suitable assignment can be found')
    parser.add_argument('--print_pl', const=True, nargs='?', type=bool, default=False, help='Print prolog statements to console')
    args = parser.parse_args()

    main(args.tile_constraints_file, args.debug, args.print_pl)
