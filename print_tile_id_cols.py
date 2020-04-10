"""
Prints list-of-lists of tile_ids (column by column) for the given level
"""


import argparse

from model.level import Level, TILE_DIM
from utils import read_pickle


def get_tile_id_cols(game, level, player_img='block'):

    # Load file
    tile_id_coords_map_filepath = "level_saved_files_%s/tile_id_coords_maps/%s/%s.pickle" % (player_img, game, level)
    tile_id_coords_map = read_pickle(tile_id_coords_map_filepath)

    coord_tile_id_map = {}
    for (tile_id, extra_info), coords in tile_id_coords_map.items():
        for coord in coords:
            coord_tile_id_map[coord] = tile_id

    # Get level dimensions
    level_w, level_h = Level.get_level_dimensions_in_tiles(game, level)
    tile_id_cols = []

    for col in range(0, level_w):
        tile_id_col = []
        for row in range(0, level_h):
            metatile_coord = (col * TILE_DIM, row * TILE_DIM)
            metatile_id = coord_tile_id_map[metatile_coord]
            tile_id_col.append(metatile_id)
        tile_id_cols.append(tile_id_col)

    return tile_id_cols  # [[col_0_tile_ids], [col_1_tile_ids], ...]


def main(game, level, column_idx, player_img):
    tile_id_cols = get_tile_id_cols(game, level, player_img)
    if column_idx is None:
        print(tile_id_cols)
    else:
        print(tile_id_cols[column_idx])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get tile ids by column')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--column_idx', type=int, help='Return tile ids for specified column only; 0-indexed]', default=None)
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    args = parser.parse_args()

    main(args.game, args.level, args.column_idx, args.player_img)
