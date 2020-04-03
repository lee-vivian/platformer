'''
A. Process a level [use pypy3 interpreter]

1. Enumerate level state graph
2. Extract level metatiles
3. Get metatile_id and id_metatile maps
4. Get {tile_id: coords} map
5. Get {metatile: num_states} map

B. Play a level [use python3 interpreter]

1. Run platformer.py
'''

import os
import argparse

import utils


def main(environment, game, level, player_img, generated_level_filepath, use_graph, draw_all_labels, draw_dup_labels,
         enumerate, extract_metatiles, get_metatile_id_map, get_tile_id_coords_map, get_states_per_metatile, process_all):

    if environment == 'maze':
        os.environ['MAZE'] = "1"
    elif environment != 'platformer':
        utils.error_exit("invalid environment - environment must be one of ['maze', 'platformer']")

    any_processing = process_all or (enumerate or extract_metatiles or get_metatile_id_map or get_tile_id_coords_map
                                     or get_states_per_metatile)

    if any_processing:

        if process_all or enumerate:
            import enumerate
            enumerate.main(game, level, player_img)

        if process_all or extract_metatiles:
            import extract_metatiles
            extract_metatiles.main(game, level, player_img, print_stats=True)

        if process_all or get_metatile_id_map:
            import get_metatile_id_map
            get_metatile_id_map.main([game], [level], player_img, outfile=None)

        if process_all or get_tile_id_coords_map:
            import get_tile_id_coords_map
            get_tile_id_coords_map.main(game, level, player_img)

        if process_all or get_states_per_metatile:
            import get_states_per_metatile
            get_states_per_metatile.main([game], [level], player_img, merge=False, outfile=None)

    else:
        import platformer
        platformer.main(game, level, player_img, generated_level_filepath, use_graph, draw_all_labels, draw_dup_labels)


if __name__ == "__main__":

    # import networkx as nx
    # from get_states_per_metatile import print_level_stats
    #
    # GAME_LEVEL_PAIRS = [
    #     ('sample', 'sample_mini'),
    #     ('sample', 'sample_small'),
    #     ('sample', 'sample_medium'),
    #     ('sample', 'sample_medium2')
    # ]
    #
    # for game, level in GAME_LEVEL_PAIRS:
    #     state_graph_filepath = "level_saved_files_block/enumerated_state_graphs/%s/%s.gpickle" % (game, level)
    #     state_graph = nx.read_gpickle(state_graph_filepath)
    #     print("LEVEL: ", level)
    #     print("Num nodes: ", len(state_graph.nodes()))
    #     print("Num edges: ", len(state_graph.edges()))
    #     print_level_stats(level)
    #     print("------------------------\n")

    # GAME_LEVEL_PAIRS = [
    #     ('sample', 'sample_mini'),
    #     ('sample', 'sample_hallway'),
    #     ('sample', 'sample_hallway_flat'),
    #     ('super_mario_bros', 'mario-1-1'),
    #     ('super_mario_bros', 'mario-2-1'),
    #     ('kid_icarus', 'kidicarus_1')
    # ]

    parser = argparse.ArgumentParser(description='Process or play a level')
    parser.add_argument('environment', type=str, help='platformer or maze')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--generated_level_filepath', type=str, help='Generated level structural txt filepath', default=None)
    parser.add_argument('--use_graph', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--draw_all_labels', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--draw_dup_labels', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--enumerate', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--extract_metatiles', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--get_metatile_id_map', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--get_tile_id_coords_map', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--get_states_per_metatile', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--process_all', const=True, nargs='?', type=bool,
                        help="Run all process scripts for the given level", default=False)

    args = parser.parse_args()

    main(args.environment, args.game, args.level, args.player_img, args.generated_level_filepath,
         args.use_graph, args.draw_all_labels, args.draw_dup_labels,
         args.enumerate, args.extract_metatiles, args.get_metatile_id_map, args.get_tile_id_coords_map,
         args.get_states_per_metatile, args.process_all)
