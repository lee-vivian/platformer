from datetime import datetime
import argparse

from model.metatile import  Metatile
from utils import read_pickle, write_pickle, get_save_directory, get_filepath, get_metatile_id


def get_tile_id_coords_map(game, level, player_img):

    # tile_id_coords_map = { (tile_id, extra_info): list-of-coords) }

    # Load saved files
    level_saved_files_dir = "level_saved_files_%s" % player_img
    metatile_coords_dict_filepath = "%s/metatile_coords_dicts/%s/%s.pickle" % (level_saved_files_dir, game, level)
    metatile_id_map_filepath = "%s/metatile_id_maps/%s.pickle" % (level_saved_files_dir, level)

    metatile_coords_dict = read_pickle(metatile_coords_dict_filepath)
    metatile_id_map = read_pickle(metatile_id_map_filepath)
    tile_id_coords_map = {}

    for metatile_str, coords in metatile_coords_dict.items():
        metatile = Metatile.from_str(metatile_str)
        metatile_id = get_metatile_id(metatile, metatile_id_map)

        extra_stuff = ""
        if not bool(metatile.graph_as_dict):  # graph is empty
            extra_stuff += "E"
        if len(coords) == 1:
            extra_stuff += "S"

        tile_id_coords_map[(metatile_id, extra_stuff)] = coords

    # Save tile_id_coords_map
    tile_id_coords_map_dir = get_save_directory("tile_id_coords_maps", player_img)
    outfile = get_filepath(tile_id_coords_map_dir, level, "pickle")
    return write_pickle(outfile, tile_id_coords_map)


def main(game, level, player_img):
    start_time = datetime.now()
    print("\nCreating {tile id: coords} for level: %s ..." % level)

    get_tile_id_coords_map(game, level, player_img)

    end_time = datetime.now()
    print("Runtime: ", end_time - start_time, "\n")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Create {tile id: coords} map for the given level')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    args = parser.parse_args()

    main(args.game, args.level, args.player_img)
