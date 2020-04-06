import re

from model.level import TILE_DIM, TILE_CHARS, GOAL_CHAR, START_CHAR, BLANK_CHAR
import utils

'''
Parse solver output line
'''


def get_assignments_dict(solution_line):
    assignments = re.findall(r'assignment\([0-9t,]*\)', solution_line)
    assignments_dict = {}  # {(tile_x, tile_y): tile_id}
    for assignment in assignments:
        match = re.match(r'assignment\((\d+),(\d+),(t\d+)\)', assignment)
        tile_x = int(match.group(1))
        tile_y = int(match.group(2))
        tile_id = match.group(3)
        assignments_dict[(tile_x, tile_y)] = tile_id
    return assignments_dict  # {(tile_x, tile_y): tile_id}


def get_fact_coord(line, fact_name):
    facts = re.findall(r'%s\([0-9t,]*\)' % fact_name, line)
    if len(facts) == 0:
        utils.error_exit("Fact '%s' not found in solver output" % fact_name)
    fact = facts[0]
    match = re.match(r'%s\((\d+),(\d+)\)' % fact_name, fact)
    x, y = int(match.group(1)), int(match.group(2))
    return x, y


'''
Create {(tile_id, extra_info): list-of-coords} map for generated level
'''


def create_tile_id_coords_map(assignments_dict, answer_set_filename, player_img, save):
    tile_id_coords_map_dir = utils.get_directory("level_saved_files_%s/tile_id_coords_maps" % player_img)
    outfile = utils.get_filepath(tile_id_coords_map_dir, "%s.pickle" % answer_set_filename)

    tile_id_coords_map = {}
    for tile_coord, tile_id in assignments_dict.items():  # {(tile_x, tile_y): tile_id}
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

    return tile_id_coords_map_with_extra_info  # {(tile_id, extra_info): list-of-coords)}


'''
Create level structural txt file for generated level
'''


def generate_level(assignments_dict, level_w, level_h, block_tile_id, start_tile_id, goal_tile_id, outfile, save):

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
