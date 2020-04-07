import networkx as nx
import argparse

from model.level import Level, TILE_DIM
from model.metatile import Metatile, METATILE_TYPES
import extract_constraints
import utils

# Acknowledgements and References:
# - Legal adjacency rules based on NPCDev groundcollapse
# - WFC in ASP implementation: based on Karth, I., & Smith, A. M. (2017). WaveFunctionCollapse is constraint solving in the wild. Proceedings of the 12th International Conference on the Foundations of Digital Games, 68. ACM.


def main(game, level, player_img, level_width, level_height, debug, print_pl, min_perc_blocks):

    print("Generating prolog file for level: %s ..." % level)

    # Use training level dimensions if level_width or level_height are None
    default_width, default_height = Level.get_level_dimensions_in_tiles(game, level)
    if level_width is None:
        level_width = default_width
    if level_height is None:
        level_height = default_height

    print("Default dimensions (%d, %d)" % (default_width, default_height))
    print("Gen dimensions (%d, %d)" % (level_width, level_height))

    # Setup save file directory
    level_prolog_dir = utils.get_directory("level_saved_files_%s/level_prolog_files" % player_img)
    outfile_name = "%s_%d_%d" % (level, level_width, level_height)
    outfile_path = utils.get_filepath(level_prolog_dir, "%s.pl" % outfile_name)

    # Get training level unique metatiles
    metatiles = Metatile.get_unique_metatiles_for_level(game, level, player_img)

    # Get training level tileset constraints dictionary
    metatile_id_map_dir = utils.get_directory("level_saved_files_%s/metatile_id_maps" % player_img)
    metatile_id_map_file = utils.get_filepath(metatile_id_map_dir, "%s.pickle" % level)
    tileset_dict = extract_constraints.get_tileset_dict(metatile_id_map_file, game, level, player_img)
    tile_constraints_dict = tileset_dict.get("tiles")

    # Generate prolog statements
    prolog_statements = ""
    prolog_statements += "dim_width(0..%d).\n" % (level_width - 1)
    prolog_statements += "dim_height(0..%d).\n" % (level_height - 1)
    prolog_statements += "dim_metatiles(1..%d).\n" % (len(metatiles))

    # Create tile facts
    create_tiles_statement = "tile(TX,TY) :- dim_width(TX), dim_height(TY)."
    prolog_statements += create_tiles_statement + "\n"

    # Limit number of metatile assignments per tile
    limit = 0 if debug else 1
    limit_metatile_per_tile_rule = "%d {assignment(TX, TY, MT) : metatile(MT) } 1 :- tile(TX,TY)." % limit
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

    # Dictionary: {metatile_type: list of metatile ids}
    metatile_type_ids = {}
    for type in METATILE_TYPES:
        metatile_type_ids[type] = []

    start_state = None
    goal_state = None

    # Create metatile facts, metatile_type facts, and legal neighbor statements for the specified tileset
    for metatile_id, metatile_info in tile_constraints_dict.items():  # for each unique metatile

        metatile_fact = "metatile(%s)." % metatile_id
        prolog_statements += metatile_fact + "\n"

        metatile_type = metatile_info.get("type")
        metatile_type_ids[metatile_type].append(metatile_id)

        metatile_graph_as_dict = eval(metatile_info.get("graph"))
        metatile_graph = nx.DiGraph(metatile_graph_as_dict)

        # Create state and link rules based on metatile graph
        for edge in metatile_graph.edges():
            src_state = eval(edge[0])
            dest_state = eval(edge[1])
            src_x, src_y, dest_x, dest_y = src_state['x'], src_state['y'], dest_state['x'], dest_state['y']

            state_rule = "state(%d+TX*%d, %d+TY*%d) :- assignment(TX,TY,%s)." % (src_x, TILE_DIM, src_y, TILE_DIM, metatile_id)
            link_rule = "link(%d+TX*%d, %d+TY*%d, %d+TX*%d, %d+TY*%d) :- assignment(TX,TY,%s)." % \
                        (src_x, TILE_DIM, src_y, TILE_DIM, dest_x, TILE_DIM, dest_y, TILE_DIM, metatile_id)

            prolog_statements += state_rule + "\n"
            prolog_statements += link_rule + "\n"

            # define start state in prolog
            if start_state is None and src_state['is_start']:
                start_rule = "start(%d+TX*%d, %d+TY*%d) :- assignment(TX,TY,%s)." % (src_x, TILE_DIM, src_y, TILE_DIM, metatile_id)
                prolog_statements += start_rule + "\n"
                start_state = src_state

            # define goal state in prolog
            if goal_state is None and src_state['goal_reached']:
                goal_rule = "goal(%d+TX*%d, %d+TY*%d) :- assignment(TX,TY,%s)." % (src_x, TILE_DIM, src_y, TILE_DIM, metatile_id)
                prolog_statements += goal_rule + "\n"
                goal_state = src_state

        # Create legal rules based on valid adjacent tiles
        for direction, adjacent_tiles in metatile_info.get("adjacent").items():  # for each adjacent dir
            DX, DY = eval(direction)

            for adjacent_id in adjacent_tiles:  # for each adjacent metatile
                legal_statement = "legal(DX, DY, MT1, MT2) :- DX == %d, DY == %d, metatile(MT1), metatile(MT2), " \
                                  "MT1 == %s, MT2 == %s." % (DX, DY, metatile_id, adjacent_id)
                prolog_statements += legal_statement + "\n"

    # Link can only exist if the src and dest states exist, otherwise solution is not valid
    link_exists_rule = ":- link(X1,Y1,X2,Y2), state(X1,Y1), not state(X2,Y2)."
    prolog_statements += link_exists_rule

    block_tile_id = metatile_type_ids.get("block")[0]
    start_tile_id = metatile_type_ids.get("start")[0]
    goal_tile_id = metatile_type_ids.get("goal")[0]

    # Start state is inherently reachable
    start_reachable_rule = "reachable(X,Y) :- start(X,Y)."
    prolog_statements += start_reachable_rule + "\n"

    # Goal state must be reachable
    goal_reachable_rule = ":- goal(X,Y), not reachable(X,Y)."
    prolog_statements += goal_reachable_rule + "\n"

    # State reachable rule
    state_reachable_rule = "reachable(X2,Y2) :- link(X1,Y1,X2,Y2), state(X1,Y2), state(X2,Y2), reachable(X1,Y1)."
    prolog_statements += state_reachable_rule + "\n"

    # Set border tiles to be block tiles
    block_tile_coords = []
    for x in range(level_width):
        block_tile_coords += [(x, 0), (x, level_height-1)]
    for y in range(level_height):
        block_tile_coords += [(0, y), (level_width-1, y)]
    for x, y in list(set(block_tile_coords)):
        block_tile_assignment = "assignment(%d, %d, %s)." % (x, y, block_tile_id)
        prolog_statements += block_tile_assignment + "\n"

    # Limit number of tiles of specified tile id
    limit_tile_type_rule = "MIN { assignment(X,Y,MT) : metatile(MT), tile(X,Y) } MAX :- limit(MT, MIN, MAX)."
    prolog_statements += limit_tile_type_rule + "\n"

    # Limit number of goal tiles
    prolog_statements += "limit(%s, 1, 1).\n" % goal_tile_id

    # Limit number of start tiles
    prolog_statements += "limit(%s, 1, 1).\n" % start_tile_id

    if min_perc_blocks is not None:
        # Limit number of block tiles
        total_tiles = int(level_width * level_height)
        prolog_statements += "limit(%s, %d, %d).\n" % (block_tile_id, int(min_perc_blocks / 100 * total_tiles), total_tiles)
        print("limit(%s, %d, %d).\n" % (block_tile_id, int(min_perc_blocks / 100 * total_tiles), total_tiles))

    # ASP WFC algorithm rule
    wfc_rule = ":- adj(X1,Y1,X2,Y2,DX,DY), assignment(X1,Y1,MT1), not 1 { assignment(X2,Y2,MT2) : legal(DX,DY,MT1,MT2) }."
    prolog_statements += wfc_rule + "\n"

    # Print
    if print_pl:
        print(prolog_statements)

    # Save
    outfile_path = utils.write_file(outfile_path, prolog_statements)

    prolog_dictionary = {
        "filename": outfile_name,
        "filepath": outfile_path,
        "level_w": level_width,  # in tile units
        "level_h": level_height,  # in tile units
        "block_tile_id": block_tile_id,
        "start_tile_id": start_tile_id,
        "goal_tile_id": goal_tile_id
    }

    print("Finished generating prolog file")

    return prolog_dictionary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Enumerate state graph for the given level')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--level_width', type=int, help='Number of tiles in a row', default=None)
    parser.add_argument('--level_height', type=int, help='Number of tiles in a column', default=None)
    parser.add_argument('--debug', const=True, nargs='?', type=bool, help='Allow blank tiles if no suitable assignment can be found', default=False)
    parser.add_argument('--print_pl', const=True, nargs='?', type=bool, help='Print prolog statements to console', default=False)
    parser.add_argument('--min_perc_blocks', type=int, help='Percent number of block tiles in a level', default=None)
    args = parser.parse_args()

    main(args.game, args.level, args.player_img, args.level_width, args.level_height, args.debug, args.print_pl, args.min_perc_blocks)
