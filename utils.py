import os
import json
import pickle
import networkx as nx
from math import sqrt, pow


def error_exit(msg):
    print(msg)
    exit(0)


def check_path_exists(filepath):
    if not os.path.exists(filepath):
        error_exit("Missing file: %s" % filepath)


def get_directory(path):
    directories = path.split("/")
    cur_dir = None
    for i in range(len(directories)):  # 0, 1, 2
        cur_dir = "/".join(directories[0:i+1])
        if not os.path.exists(cur_dir):
            os.makedirs(cur_dir)
    return cur_dir


def get_filepath(directory, file):
    dir = get_directory(directory)
    return os.path.join(dir, file)


def read_json(filepath):
    check_path_exists(filepath)
    with open(filepath, 'r') as file:
        contents = json.load(file)
    file.close()
    return contents


def write_json(filepath, contents):
    with open(filepath, 'w') as file:
        json.dump(contents, file, indent=2, sort_keys=True)
    file.close()
    print("Saved to:", filepath)
    return filepath


def read_pickle(filepath):
    check_path_exists(filepath)
    with open(filepath, 'rb') as file:
        contents = pickle.load(file)
    file.close()
    return contents


def write_pickle(filepath, contents):
    with open(filepath, 'wb') as file:
        pickle.dump(contents, file, protocol=pickle.HIGHEST_PROTOCOL)
    file.close()
    print("Saved to:", filepath)
    return filepath


def write_file(filepath, statements):
    with open(filepath, 'w') as file:
        file.write("%s" % statements)
    file.close()
    print("Saved to:", filepath)
    return filepath


def all_equal(list):
    return all(i == list[0] for i in list)


def list_to_dict(list):
    dictionary = {}
    for item in list:
        dictionary[item] = 1
    return dictionary


def euclidean_distance(coord_a, coord_b):
    x1, y1 = coord_a
    x2, y2 = coord_b
    return int(sqrt(pow(x1-x2, 2) + pow(y1-y2, 2)))


def get_all_indices(item, list):
    return [i for i, x in enumerate(list) if x == item]

# def state_in_metatile(metatile_coord, state_coord, half_player_w, half_player_h, tile_dim):
#     return metatile_coord == metatile_coord_from_state_coord(state_coord, half_player_w, half_player_h, tile_dim)


def get_node_xy(node):
    state_dict = eval(node)
    return state_dict['x'], state_dict['y']


def get_node_at_coord(graph, coord):
    for node in graph.nodes():
        if get_node_xy(node) == coord:
            return node
    return None


def get_start_and_goal_states(state_graph):
    start_states = []
    goal_states = []
    for node in state_graph.nodes():
        state_dict = eval(node)
        if state_dict.get("is_start"):
            start_states.append(node)
        elif state_dict.get("goal_reached"):
            goal_states.append(node)
    return start_states, goal_states


def shortest_path_xy(state_graph):
    start_states, goal_states = get_start_and_goal_states(state_graph)

    if len(start_states) < 1:
        error_exit("No start states found in state graph")

    if len(goal_states) < 1:
        error_exit("No goal states found in state graph")

    for src in start_states:
        for dest in goal_states:
            if nx.has_path(state_graph, src, dest):
                shortest_path = nx.dijkstra_path(state_graph, src, dest, weight='weight')
                return [get_node_xy(node) for node in shortest_path]

    error_exit("No solution path found in state graph")
