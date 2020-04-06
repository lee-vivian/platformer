import networkx as nx
from datetime import datetime

from model.metatile import Metatile


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


def validate_generated_level(level_dictionary, id_metatile_map):
    tile_id_extra_info_coords_map = level_dictionary.get("tile_id_extra_info_coords_map")
    start_coord = level_dictionary.get("start_coord")
    goal_coord = level_dictionary.get("goal_coord")

    level_state_graph = create_state_graph(tile_id_extra_info_coords_map, id_metatile_map)

    return check_path_exists(level_state_graph, start_coord, goal_coord)


def validate_generated_levels(gen_level_dict, id_metatile_map):
    print("Validating generated levels...")
    start_time = datetime.now()
    invalid_level_count = 0
    for level_name, level_dictionary in gen_level_dict.items():
        level_is_valid = validate_generated_level(level_dictionary, id_metatile_map)
        if not level_is_valid:
            print("Invalid level: %s" % level_name)
            invalid_level_count += 1
    print("Number invalid levels: %d" % invalid_level_count)
    end_time = datetime.now()
    print("Time to create state graphs and validate levels: %s" % str(end_time-start_time))
