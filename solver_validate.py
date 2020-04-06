import networkx as nx
from datetime import datetime

from model.metatile import Metatile
from utils import get_save_directory, get_filepath, write_pickle, read_pickle


'''
Create and validate generated level state graph
'''


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


def get_node_xy(node):
    state_dict = eval(node)
    return state_dict['x'], state_dict['y']


def get_node_at_coord(graph, coord):
    for node in graph.nodes():
        if get_node_xy(node) == coord:
            return node
    return None


def get_level_components(level_dictionary, id_metatile_map):
    tile_id_extra_info_coords_map = level_dictionary.get("tile_id_extra_info_coords_map")
    start_coord = level_dictionary.get("start_coord")
    goal_coord = level_dictionary.get("goal_coord")

    state_graph = create_state_graph(tile_id_extra_info_coords_map, id_metatile_map)
    src_node = get_node_at_coord(state_graph, start_coord)
    dest_node = get_node_at_coord(state_graph, goal_coord)

    return state_graph, src_node, dest_node


def shortest_path_xy(state_graph, src_node, dest_node):
    shortest_path = nx.shortest_path(state_graph, src_node, dest_node)
    return [get_node_xy(node) for node in shortest_path]


def main(gen_level_dict, id_metatile_map, player_img):
    print("Validating generated levels...")
    start_time = datetime.now()
    invalid_level_count = 0

    generated_levels_paths = get_save_directory("generated_levels_paths", player_img)

    for level_name, level_dictionary in gen_level_dict.items():
        state_graph, src_node, dest_node = get_level_components(level_dictionary, id_metatile_map)
        valid_level = nx.has_path(state_graph, src_node, dest_node)
        if valid_level:
            shortest_path = shortest_path_xy(state_graph, src_node, dest_node)
            outfile = get_filepath(generated_levels_paths, level_name, "pickle")
            write_pickle(outfile, shortest_path)
            print(read_pickle(outfile))
        else:
            print("Invalid level: %s" % level_name)
            invalid_level_count += 1

    print("Number invalid levels: %d" % invalid_level_count)
    end_time = datetime.now()
    print("Time to create state graphs and validate levels: %s" % str(end_time-start_time))
