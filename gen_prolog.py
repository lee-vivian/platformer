import argparse

from model.level import Level
from model.metatile import Metatile
import extract_constraints
import utils

# Acknowledgements and References:
# - Legal adjacency rules based on NPCDev groundcollapse
# - WFC in ASP implementation: based on Karth, I., & Smith, A. M. (2017). WaveFunctionCollapse is constraint solving in the wild. Proceedings of the 12th International Conference on the Foundations of Digital Games, 68. ACM.


DEBUG_MODE = False  # allows tiles to be blank if no suitable assignment can be found
PRINT_PROLOG = False  # print prolog statements to console


def main(game, level, player_img, level_width, level_height):

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
    level_prolog_dir = utils.get_save_directory("level_prolog_files", player_img)
    outfile = utils.get_filepath(level_prolog_dir, "%s_%d_%d" % (level, level_width, level_height), "pl")

    # Get training level unique metatiles
    metatiles = Metatile.get_unique_metatiles_for_level(game, level, player_img)

    # Get training level tileset constraints dictionary
    metatile_id_map_dir = utils.get_save_directory("metatile_id_maps", player_img)
    metatile_id_map_file = utils.get_filepath(metatile_id_map_dir, level, "pickle")
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
    limit = 0 if DEBUG_MODE else 1
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

    # Create metatile facts and legal neighbor statements for the specified tileset
    for metatile_id, metatile_info in tile_constraints_dict.items():  # for each unique metatile

        metatile_fact = "metatile(%s)." % metatile_id
        prolog_statements += metatile_fact + "\n"

        for direction, adjacent_tiles in metatile_info.get("adjacent").items():  # for each adjacent dir

            DX, DY = eval(direction)

            for adjacent_id in adjacent_tiles:  # for each adjacent metatile

                legal_statement = "legal(DX, DY, MT1, MT2) :- DX == %d, DY == %d, metatile(MT1), metatile(MT2), " \
                                  "MT1 == %s, MT2 == %s." % (DX, DY, metatile_id, adjacent_id)
                prolog_statements += legal_statement + "\n"

    # ASP WFC algorithm rule
    wfc_rule = ":- adj(X1,Y1,X2,Y2,DX,DY), assignment(X1,Y1,MT1), not 1 { assignment(X2,Y2,MT2) : legal(DX,DY,MT1,MT2) }."
    prolog_statements += wfc_rule + "\n"

    # Print
    if PRINT_PROLOG:
        print(prolog_statements)

    # Save
    utils.write_prolog(outfile, prolog_statements)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Enumerate state graph for the given level')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--level_width', type=int, help='Number of tiles in a row', default=None)
    parser.add_argument('--level_height', type=int, help='Number of tiles in a column', default=None)
    args = parser.parse_args()

    main(args.game, args.level, args.player_img, args.level_width, args.level_height)
