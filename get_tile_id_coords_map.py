from datetime import datetime
import argparse

from model.metatile import Metatile
from utils import read_pickle, write_pickle, get_filepath, error_exit


def main(game, level, metatile_coords_dict_file, metatile_id_map_file, player_img):

    start_time = datetime.now()
    print("\nCreating {(tile id, extra_info): coords} map ...")

    metatile_coords_dict = read_pickle(metatile_coords_dict_file)
    metatile_id_map = read_pickle(metatile_id_map_file)
    tile_id_extra_info_coords_map = {}

    for metatile_str, coords in metatile_coords_dict.items():
        metatile = Metatile.from_str(metatile_str)
        metatile_id = metatile_id_map.get(metatile_str)
        if metatile_id is None:
            error_exit("metatile_str not found in metatile_id_map")
        has_graph = bool(metatile.graph_as_dict)
        extra_info = ""
        if not has_graph:
            extra_info += "E"  # metatile graph is empty
        if len(coords) == 1:
            extra_info += "S"  # metatile was only used for one tile

        tile_id_extra_info_coords_map[(metatile_id, extra_info)] = coords

    save_directory = "level_saved_files_%s/tile_id_coords_maps/%s/" % (player_img, game)
    save_file = get_filepath(save_directory, "%s.pickle" % level)
    write_pickle(save_file, tile_id_extra_info_coords_map)

    end_time = datetime.now()
    print("Runtime: ", end_time - start_time, "\n")

    return save_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create {tile id: coords} map from the given files')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('metatile_coords_dict_file', type=str, help="File path of the metatile_coords dict to use")
    parser.add_argument('metatile_id_map_file', type=str, help="File path of the metatile_id map to use")
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    args = parser.parse_args()

    main(args.game, args.level, args.metatile_coords_dict_file, args.metatile_id_map_file, args.player_img)
