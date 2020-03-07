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


def main(game, level, player_img, process):

    if process:
        import enumerate
        import extract_metatiles
        import get_metatile_id_map
        import extract_constraints

        enumerate.main(game, level, player_img)
        extract_metatiles.main(game, level, player_img, True)
        id_metatile_file, metatile_id_file = get_metatile_id_map.main([game], [level], player_img, None)
        tileset_constraints_file = extract_constraints.main(metatile_id_file, [game], [level], player_img, None)
        return tileset_constraints_file

    else:
        import platformer

        platformer.main(game, level, player_img, False, False, False)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Process or play a level')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--process', type=bool, help="Run process scripts for the given level", default=False)
    args = parser.parse_args()

    main(args.game, args.level, args.player_img, args.process)
