import argparse

from model.level import Level, TILE_DIM
from utils import read_pickle


def get_tile_id_cols(game, level, player_img='block'):

    # Get level dimensions
    level_obj = Level.generate_level_from_file("%s/%s.txt" % (game, level))
    level_w = int(level_obj.get_width() / TILE_DIM)
    level_h = int(level_obj.get_height() / TILE_DIM)

    # Load saved file
    tile_id_coords_map_filepath = "level_saved_files_%s/tile_id_coords_maps/%s.pickle" % (player_img, level)
    tile_id_coords_map = read_pickle(tile_id_coords_map_filepath)

    coord_tile_id_map = {}
    for (tile_id, extra_info), coords in tile_id_coords_map.items():
        for coord in coords:
            coord_tile_id_map[coord] = tile_id

    # Get tile ids for level (list of column-lists top-down)
    tile_id_cols = []
    for col in range(0, level_w-1):
        tile_id_col = []
        for row in range(0, level_h-1):
            metatile_coord = (col * TILE_DIM, row * TILE_DIM)
            metatile_id = coord_tile_id_map[metatile_coord]
            tile_id_col.append(metatile_id)
        tile_id_cols.append(tile_id_col)

    return tile_id_cols


def main(game, level, column, player_img):
    tile_id_cols = get_tile_id_cols(game, level, player_img)
    if column is None:
        print(tile_id_cols)
    else:
        print(tile_id_cols[column])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get tile ids by column')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('column', type=int, help='Return tile ids for specified column only; 0-indexed]', default=None)
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    args = parser.parse_args()

    main(args.game, args.level, args.column, args.player_img)
