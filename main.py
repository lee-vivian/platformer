"""
A. Process a level [use pypy3 interpreter]
B. Play a level [use python3 interpreter]
"""

import os
import argparse

import utils

ENVIRONMENTS = ['maze', 'example', 'platformer']


def main(environment, game, level, player_img, use_graph, draw_all_labels, draw_dup_labels, draw_path, show_score,
         process, dimensions, structure, summary):

    # Set environment variable
    if environment not in ENVIRONMENTS:
        utils.error_exit("invalid environment - environment must be one of %s" % str(ENVIRONMENTS))
    if environment == 'maze':
        os.environ['MAZE'] = "1"
    elif environment == 'example':
        os.environ['EXAMPLE'] = "1"

    if dimensions or structure or summary:
        from model.level import Level
        if dimensions:
            print(Level.get_level_dimensions_in_tiles(game, level))
        if structure:
            Level.print_structural_txt(game, level)
        if summary:
            Level.print_tile_summary(game, level)
        exit(0)

    if process:
        import enumerate
        state_graph_file = enumerate.main(game, level, player_img)

        import extract_metatiles
        unique_metatiles_file, metatile_coords_dict_file = extract_metatiles.main(save_filename=level,
                                                                                  player_img=player_img,
                                                                                  print_stats=False,
                                                                                  state_graph_files=[state_graph_file])

        import get_metatile_id_map
        id_metatile_map_file, metatile_id_map_file = get_metatile_id_map.main(save_filename=level,
                                                                              unique_metatiles_file=unique_metatiles_file,
                                                                              player_img=player_img)

        import get_tile_id_coords_map
        get_tile_id_coords_map.main(game, level, metatile_coords_dict_file, metatile_id_map_file, player_img)

        import get_states_per_metatile
        get_states_per_metatile.main(save_filename=level, unique_metatiles_file=unique_metatiles_file,
                                     player_img=player_img, print_stats=False)

        import extract_constraints
        metatile_constraints_file = extract_constraints.main(save_filename=level, metatile_id_map_file=metatile_id_map_file,
                                                             id_metatile_map_file=id_metatile_map_file,
                                                             metatile_coords_dict_files=[metatile_coords_dict_file],
                                                             player_img=player_img)

        import gen_prolog
        prolog_file = gen_prolog.main(tile_constraints_file=metatile_constraints_file, debug=False, print_pl=False)


    else:
        import platformer
        platformer.main(game, level, player_img, use_graph, draw_all_labels, draw_dup_labels, draw_path, show_score)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process or play a level')
    parser.add_argument('environment', type=str, help='platformer or maze')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--use_graph', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--draw_all_labels', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--draw_dup_labels', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--draw_path', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--show_score', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--process', const=True, nargs='?', type=bool, help="Run process scripts", default=False)
    parser.add_argument('--dimensions', const=True, nargs='?', type=bool, help="Get level dimensions in tiles (width, height)", default=False)
    parser.add_argument('--structure', const=True, nargs='?', type=bool, help="Print level txt structural layer", default=False)
    parser.add_argument('--summary', const=True, nargs='?', type=bool, help="Print level tile summmary stats", default=False)

    args = parser.parse_args()

    main(args.environment, args.game, args.level, args.player_img,
         args.use_graph, args.draw_all_labels, args.draw_dup_labels, args.draw_path, args.show_score,
         args.process, args.dimensions, args.structure, args.summary)
