import argparse

from model.level import Level
from model.metatile import Metatile
import utils


def main(game, level, player_img, level_width, level_height):

    # Setup save file directory
    level_saved_files_dir = "level_saved_files_%s" % player_img
    level_prolog_dir = utils.get_save_directory(level_saved_files_dir, "level_prolog_files")
    outfile = utils.get_filepath(level_prolog_dir, level, "txt")

    # Use training level dimensions if level_width or level_height are None
    default_width, default_height = Level.generate_level_from_file(game, level)
    if level_width is None:
        level_width = default_width
    if level_height is None:
        level_height = default_height

    metatiles = Metatile.get_unique_metatiles_for_level(game, level, player_img)

    # Generate prolog statements
    prolog_statements = ""
    prolog_statements += "dim_width(0..%d).\n" % (level_width - 1)
    prolog_statements += "dim_height(0..%d).\n" % (level_height - 1)
    prolog_statements += "dim_metatiles(1..%d).\n" % (len(metatiles))

    create_tiles_statement = "tile((TX,TY)) :- dim_width(TX), dim_height(TY)."
    prolog_statements += create_tiles_statement + "\n"

    # @TODO - create metatile facts from tileset (e.g. metatile(tileName).

    one_metatile_per_tile_statement = "1 {assign(T, MT) : metatile(MT) } 1:- tile(T)."
    prolog_statements += one_metatile_per_tile_statement + "\n"


    # Print
    print(prolog_statements)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Enumerate state graph for the given level')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--level_width', type=int, help='Number of tiles in a row', default=None)
    parser.add_argument('--level_height', type=int, help='Number of tiles in a column', default=None)
    args = parser.parse_args()

    main(args.game, args.level, args.player_img, args.level_width, args.level_height)
