'''
A. Process a level [use pypy3 interpreter]

1. Enumerate level state graph
2. Extract level metatiles
3. Get metatile_id and id_metatile map for level(s)
4. Extract tileset constraints for level(s)

B. Play a level [use python3 interpreter]

1. Run platformer.py
'''

import argparse

from utils import error_exit


def main(game, level, player_img, enumerate, extract_metatiles, get_metatile_id_map, get_states_per_metatile,
         extract_constraints, process_all):

    any_processing = process_all or (enumerate or extract_metatiles or get_metatile_id_map or get_states_per_metatile
                                     or extract_constraints)

    if any_processing:

        id_metatile_file, metatile_id_file = None, None

        if process_all or enumerate:
            import enumerate
            enumerate.main(game, level, player_img)

        if process_all or extract_metatiles:
            import extract_metatiles
            extract_metatiles.main(game, level, player_img, print_stats=True)

        if process_all or get_metatile_id_map:
            import get_metatile_id_map
            id_metatile_file, metatile_id_file = get_metatile_id_map.main([game], [level], player_img, outfile=None)

        if process_all or get_states_per_metatile:
            import get_states_per_metatile
            get_states_per_metatile.main([game], [level], player_img, merge=False, outfile=None)

        if process_all or extract_constraints:
            if metatile_id_file is None:
                error_exit("The metatile_id file for %s: level %s does not exist. "
                           "Run get_metatile_id_map script first." % (game, level))
            import extract_constraints
            extract_constraints.main(metatile_id_file, [game], [level], player_img, outfile=None)

    else:
        import platformer
        platformer.main(game, level, player_img, use_graph=False, draw_labels=False, draw_dup_labels_only=False)


if __name__ == "__main__":

    # GAME_LEVEL_PAIRS = [
    #     ('sample', 'sample_mini'),
    #     ('sample', 'sample_hallway'),
    #     ('sample', 'sample_hallway_flat'),
    #     ('super_mario_bros', 'mario-1-1'),
    #     ('super_mario_bros', 'mario-2-1'),
    #     ('kid_icarus', 'kidicarus_1')
    # ]
    #
    # for game, level in GAME_LEVEL_PAIRS:
    #     main(game, level, player_img='block', enumerate=False, extract_metatiles=True, get_metatile_id_map=True,
    #          get_states_per_metatile=True, extract_constraints=True, process_all=False)

    parser = argparse.ArgumentParser(description='Process or play a level')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--enumerate', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--extract_metatiles', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--get_metatile_id_map', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--extract_constraints', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--get_states_per_metatile', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--process_all', const=True, nargs='?', type=bool,
                        help="Run all process scripts for the given level", default=False)

    args = parser.parse_args()

    main(args.game, args.level, args.player_img, args.enumerate, args.extract_metatiles, args.get_metatile_id_map,
         args.extract_constraints, args.get_states_per_metatile, args.process_all)
