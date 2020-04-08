'''
Enumerate the state space of a level and extract level metatiles
'''

# Note: use pypy3 to run; use pip_pypy3 to install third-party packages (e.g. networkx)

import networkx as nx
from datetime import datetime
import argparse

from model.metatile import Metatile, METATILE_TYPES
from model.level import Level, TILE_DIM
from enumerate import parse_state_graph_filename
import utils


def get_unique_metatiles_file(save_filename, player_img):
    level_saved_files_dir = "level_saved_files_%s/" % player_img
    save_file = "%s.pickle" % save_filename
    unique_metatiles_file = utils.get_filepath(level_saved_files_dir + "unique_metatiles", save_file)
    return unique_metatiles_file


def get_metatile_coords_dict_file(save_filename, player_img):
    level_saved_files_dir = "level_saved_files_%s/" % player_img
    save_file = "%s.pickle" % save_filename
    metatile_coords_dict_file = utils.get_filepath(level_saved_files_dir + "metatile_coords_dicts", save_file)
    return metatile_coords_dict_file


def get_metatile_coord_states_map(state_graph, all_possible_coords):
    metatile_coord_states_map = {}
    for coord in all_possible_coords:
        metatile_coord_states_map[coord] = []

    for node in state_graph.nodes():
        state_dict = eval(node)
        state_coord = (state_dict['x'], state_dict['y'])
        metatile_coord = Metatile.get_metatile_coord_from_state_coord(state_coord, TILE_DIM)
        if metatile_coord_states_map.get(metatile_coord) is None:
            utils.error_exit("State coord is outside of the level bounds")
        else:
            metatile_coord_states_map[metatile_coord].append(node)
    return metatile_coord_states_map


def construct_metatile(metatile_coord, level_start_coord, level_goal_coords_dict, level_platform_coords_dict,
                       state_graph, metatile_coord_states_map):
    # Determine metatile type
    if metatile_coord == level_start_coord:
        metatile_type = 'start'
    elif level_goal_coords_dict.get(metatile_coord) is not None:
        metatile_type = 'goal'
    elif level_platform_coords_dict.get(metatile_coord) is not None:
        metatile_type = 'block'
    else:
        metatile_type = 'blank'

    # Construct metatile graph
    metatile_graph = nx.DiGraph()
    states_in_metatile = metatile_coord_states_map.get(metatile_coord)

    for state in states_in_metatile:
        subgraph = state_graph.edge_subgraph(state_graph.edges(state)).copy()
        metatile_graph = nx.compose(metatile_graph, subgraph)  # join graphs

    # Normalize metatile_graph to metatile_coord
    if len(states_in_metatile) > 0:
        metatile_graph = Metatile.get_normalized_graph(metatile_graph, metatile_coord, normalize=True)

    # Construct new Metatile obj
    metatile_graph_as_dict = nx.to_dict_of_dicts(metatile_graph)
    return Metatile(metatile_type, metatile_graph_as_dict)


def extract_metatiles(state_graph_files, unique_metatiles_file, metatile_coords_dict_file):

    all_metatiles = []
    unique_metatiles = []
    metatile_str_metatile_dict = {}
    metatile_coords_dict = {}

    for state_graph_file in state_graph_files:

        # Load in the state graph
        state_graph = nx.read_gpickle(state_graph_file)

        # Extract game and level from state graph filename
        level_info = parse_state_graph_filename(state_graph_file)
        game, level = level_info['game'], level_info['level']

        # Generate level object from file
        level_obj = Level.generate_level_from_file(game, level)

        # Create dictionaries for level platform coords and goal coords
        platform_coords_dict = utils.list_to_dict(level_obj.get_platform_coords())
        goal_coords_dict = utils.list_to_dict(level_obj.get_goal_coords())

        # Extract metatiles from level
        all_possible_coords = level_obj.get_all_possible_coords()
        metatile_coord_states_map = get_metatile_coord_states_map(state_graph, all_possible_coords)

        for metatile_coord in all_possible_coords:

            new_metatile = construct_metatile(metatile_coord,
                                              level_start_coord=level_obj.get_start_coord(),
                                              level_goal_coords_dict=goal_coords_dict,
                                              level_platform_coords_dict=platform_coords_dict,
                                              state_graph=state_graph,
                                              metatile_coord_states_map=metatile_coord_states_map)

            # Add new_metatile to list of all_metatiles
            all_metatiles.append(new_metatile)

            # Add new_metatile to list of unique metatiles if it hasn't been added yet
            new_metatile_str = new_metatile.to_str()
            if new_metatile not in unique_metatiles:
                unique_metatiles.append(new_metatile)
                metatile_str_metatile_dict[new_metatile_str] = new_metatile

            # Create {metatile: coords} dictionary
            if metatile_coords_dict_file is not None:
                for metatile_str, metatile in metatile_str_metatile_dict.items():
                    if metatile == new_metatile:
                        new_metatile_str = metatile_str  # get standardized metatile str
                        break
                if metatile_coords_dict.get(new_metatile_str) is None:
                    metatile_coords_dict[new_metatile_str] = [metatile_coord]
                else:
                    metatile_coords_dict[new_metatile_str].append(metatile_coord)

    # Save {metatile: coords} dict to file
    if metatile_coords_dict_file is not None:
        utils.write_pickle(metatile_coords_dict_file, metatile_coords_dict)

    # Save unique metatiles to file
    utils.write_pickle(unique_metatiles_file, unique_metatiles)

    return all_metatiles, unique_metatiles


def get_metatile_stats_dict(all_metatiles, unique_metatiles):

    stats_dict = {"num_total_metatiles": 0,
                  "num_metatiles_with_graphs": 0,
                  "num_unique_metatiles": 0,
                  "num_unique_metatiles_with_graphs": 0}

    for type in METATILE_TYPES:
        metatile_type_key = "num_%s_metatiles" % type
        stats_dict[metatile_type_key] = 0

    for metatile in all_metatiles:
        stats_dict["num_total_metatiles"] += 1
        stats_dict["num_%s_metatiles" % metatile.type] += 1

        has_graph = bool(metatile.graph_as_dict)
        if has_graph:
            stats_dict["num_metatiles_with_graphs"] += 1

    for unique_metatile in unique_metatiles:
        stats_dict["num_unique_metatiles"] += 1
        has_graph = bool(unique_metatile.graph_as_dict)
        if has_graph:
            stats_dict["num_unique_metatiles_with_graphs"] += 1

    return stats_dict


def main(save_filename, player_img, print_stats, state_graph_files):

    unique_metatiles_file = get_unique_metatiles_file(save_filename, player_img)

    # Only construct metatile_coords dictionary if extracting metatiles from ONE state graph (one level)
    if len(state_graph_files) == 1:
        metatile_coords_dict_file = get_metatile_coords_dict_file(save_filename, player_img)
    else:
        metatile_coords_dict_file = None

    # Extract metatiles from state graph files
    print("Extracting metatiles ...")
    start_time = datetime.now()
    all_metatiles, unique_metatiles = extract_metatiles(state_graph_files, unique_metatiles_file, metatile_coords_dict_file)
    end_time = datetime.now()
    print("Runtime: %s" % str(end_time-start_time))

    # Calculate Level Metatile Stats
    if print_stats:
        print("Calculating stats for extracted metatiles...")
        start_time = datetime.now()

        metatile_stats_dict = get_metatile_stats_dict(all_metatiles, unique_metatiles)
        print("---- Stats for Extracted Metatiles ----")
        for key in metatile_stats_dict.keys():
            print(key, ": ", metatile_stats_dict.get(key))

        end_time = datetime.now()
        print("Runtime: %s" % str(end_time-start_time))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract metatiles from the given state graph file(s)')
    parser.add_argument('save_filename', type=str, help='File name to save extracted info to')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    parser.add_argument('--print_stats', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--state_graph_files', type=str, nargs='+', help='State graph file paths')
    args = parser.parse_args()

    main(args.save_filename, args.player_img, args.print_stats, args.state_graph_files)


