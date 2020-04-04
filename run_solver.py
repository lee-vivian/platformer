import subprocess
import os
import re
import argparse
import networkx as nx
from datetime import datetime

import gen_prolog
import utils
import get_metatile_id_map
from model.metatile import Metatile
from model.level import TILE_DIM, TILE_CHARS, GOAL_CHAR, START_CHAR, BLANK_CHAR


def get_assignments_dict(solution_line):
    # Extract tile x, y, and id from assignment string in solver output line
    assignments = re.findall(r'assignment\([0-9t,]*\)', solution_line)
    assignments_dict = {}  # {(tile_x, tile_y): tile_id}
    for assignment in assignments:
        match = re.match(r'assignment\((\d+),(\d+),(t\d+)\)', assignment)
        tile_x = int(match.group(1))
        tile_y = int(match.group(2))
        tile_id = match.group(3)
        assignments_dict[(tile_x, tile_y)] = tile_id
    return assignments_dict


# Used to draw metatile labels on generated level
# input: assignments dict {(tile_x, tile_y): tile_id}
# output: tile_id_coords_map {(tile_id, extra_info): list-of-coords)}
def create_tile_id_coords_map(assignments_dict, answer_set_filename, player_img, save):
    tile_id_coords_map_dir = utils.get_save_directory("tile_id_coords_maps", player_img)
    outfile = utils.get_filepath(tile_id_coords_map_dir, answer_set_filename, "pickle")

    tile_id_coords_map = {}
    for tile_coord, tile_id in assignments_dict.items():
        if tile_id_coords_map.get(tile_id) is None:
            tile_id_coords_map[tile_id] = []
        metatile_coord = (tile_coord[0] * TILE_DIM, tile_coord[1] * TILE_DIM)
        tile_id_coords_map[tile_id].append(metatile_coord)

    tile_id_coords_map_with_extra_info = {}
    for tile_id, coords in tile_id_coords_map.items():
        extra_info = "S" if len(coords) == 1 else ""
        tile_id_coords_map_with_extra_info[(tile_id, extra_info)] = coords

    if save:
        utils.write_pickle(outfile, tile_id_coords_map_with_extra_info)

    return tile_id_coords_map_with_extra_info


def create_state_graph(tile_id_extra_info_coords_map, id_metatile_map):

    state_graph = nx.DiGraph()

    for (tile_id, extra_info), coords in tile_id_extra_info_coords_map.items():
        metatile_dict = eval(id_metatile_map.get(tile_id))
        metatile_state_graph = nx.DiGraph(metatile_dict.get('graph'))
        if nx.is_empty(metatile_state_graph):
            continue
        for coord in coords:
            unnormalized_metatile_state_graph = Metatile.get_normalized_graph(metatile_state_graph, coord, normalize=False)
            state_graph = nx.compose(state_graph, unnormalized_metatile_state_graph)

    return state_graph


def get_fact_coord(line, fact_name):
    facts = re.findall(r'%s\([0-9t,]*\)' % fact_name, line)
    if len(facts) == 0:
        utils.error_exit("Fact '%s' not found in solver output" % fact_name)
    fact = facts[0]
    match = re.match(r'%s\((\d+),(\d+)\)' % fact_name, fact)
    x, y = int(match.group(1)), int(match.group(2))
    return x, y


def get_node_at_coord(graph, coord):
    for node in graph.nodes():
        state_dict = eval(node)
        if (state_dict['x'], state_dict['y']) == coord:
            return node
    return None


def check_path_exists(state_graph, start_coord, goal_coord):
    src_node = get_node_at_coord(state_graph, start_coord)
    dest_node = get_node_at_coord(state_graph, goal_coord)
    return nx.has_path(state_graph, src_node, dest_node)


def generate_level(assignments_dict, outfile, save, level_w, level_h, block_tile_id, start_tile_id, goal_tile_id):

    def get_tile_char(tile_id):
        if tile_id == block_tile_id:
            return TILE_CHARS[0]
        elif tile_id == start_tile_id:
            return START_CHAR
        elif tile_id == goal_tile_id:
            return GOAL_CHAR
        else:
            return BLANK_CHAR

    # Generate structural txt file for new level
    level_structural_txt = ""
    for row in range(level_h):
        for col in range(level_w):
            tile_xy = (col, row)
            tile_id = assignments_dict.get(tile_xy)
            tile_char = get_tile_char(tile_id)
            level_structural_txt += tile_char
        level_structural_txt += "\n"

    # Print
    print(level_structural_txt)
    # Save structural txt file to given outfile path
    if save:
        utils.write_file(outfile, level_structural_txt)
    return True


def main(game, level, player_img, level_w, level_h, debug, max_sol, skip_print_answers, save):

    # Generate prolog file for level and return prolog dictionary
    prolog_dictionary = gen_prolog.main(game, level, player_img, level_w, level_h, debug, print_pl=False)

    # Get id_metatile map for level
    id_metatile_map = get_metatile_id_map.main([game], [level], player_img, outfile=None,
                                               save=False).get("id_metatile_map")

    # Create new directory for generated levels
    generated_levels_dir = utils.get_save_directory("generated_levels", player_img)

    # Get command to run clingo solver
    clingo_cmd = "clingo %d %s " % (max_sol, prolog_dictionary.get("filepath"))
    if skip_print_answers:
        clingo_cmd += "--quiet"

    # Track solver output
    solver_line_count = 0
    answer_set_count = 0
    answer_set_line_idx = {}

    print("Running: %s" % clingo_cmd)
    start = datetime.now()

    try:
        # Run subprocess command and process each stdout line
        process = subprocess.Popen(clingo_cmd, shell=True, stdout=subprocess.PIPE)
        for line_bytes in iter(process.stdout.readline, b''):

            line = line_bytes.decode('utf-8')
            if 'Answer' in line:  # the next line contains an answer set
                answer_set_line_idx[solver_line_count+1] = 1

            if answer_set_line_idx.get(solver_line_count) is not None:  # this line contains an answer set
                answer_set_filename = "%s_a%d" % (prolog_dictionary.get("filename"), answer_set_count)
                answer_set_filepath = os.path.join(generated_levels_dir, answer_set_filename + ".txt")

                assignments_dict = get_assignments_dict(line)  # {(tile_x, tile_y): tile_id}

                # Used to draw metatile labels
                tile_id_extra_info_coords_map = create_tile_id_coords_map(assignments_dict, answer_set_filename,
                                                                          player_img, save=save)

                # Create state graph for generated level
                level_state_graph = create_state_graph(tile_id_extra_info_coords_map, id_metatile_map)

                # Check if generated level contains valid path from start to goal
                start_coord = get_fact_coord(line, 'start')
                goal_coord = get_fact_coord(line, 'goal')
                path_exists = check_path_exists(level_state_graph, start_coord, goal_coord)
                if not path_exists:
                    utils.error_exit("No valid path for generated level %s" % answer_set_filename)
                else:
                    print("Generated level %s is valid" % answer_set_filename)

                # create level structural txt file for the answer set
                generate_level(assignments_dict, outfile=answer_set_filepath, save=save,
                               level_w=prolog_dictionary.get("level_w"), level_h=prolog_dictionary.get("level_h"),
                               block_tile_id=prolog_dictionary.get("block_tile_id"),
                               start_tile_id=prolog_dictionary.get("start_tile_id"),
                               goal_tile_id=prolog_dictionary.get("goal_tile_id"))
                answer_set_count += 1

            solver_line_count += 1

        print("Num Levels Generated: %d" % answer_set_count)
        end = datetime.now()
        print("Total Runtime %s" % str(end-start))

    except KeyboardInterrupt:
        print("Num Levels Generated: %d" % answer_set_count)
        end = datetime.now()
        print("Total Runtime %s" % str(end - start))
        exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run solver and save valid answer sets as new levels')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--level_w', type=int, help='Number of tiles in a row', default=None)
    parser.add_argument('--level_h', type=int, help='Number of tiles in a column', default=None)
    parser.add_argument('--debug', const=True, nargs='?', type=bool, help='Allow blank tiles if no suitable assignment can be found', default=False)
    parser.add_argument('--max_sol', type=int, help='Maximum number of solutions to solve for; 0 = all', default=0)
    parser.add_argument('--skip_print_answers', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--save', const=True, nargs='?', type=bool, default=False)

    args = parser.parse_args()
    main(args.game, args.level, args.player_img, args.level_w, args.level_h,
         args.debug, args.max_sol, args.skip_print_answers, args.save)
