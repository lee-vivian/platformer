import os
import json
import pickle
import networkx as nx


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


def get_save_directory(dir_name, player_img='block'):

    level_saved_files_dir = "level_saved_files_%s" % player_img
    if not os.path.exists(level_saved_files_dir):
        os.makedirs(level_saved_files_dir)

    save_dir_path = os.path.join(level_saved_files_dir, dir_name)
    if not os.path.exists(save_dir_path):
        os.makedirs(save_dir_path)

    return save_dir_path


def get_save_subdirectory(parent_dir_name, subdir_name, player_img='block'):
    parent_dir_path = get_save_directory(parent_dir_name, player_img)
    subdir_path = os.path.join(parent_dir_path, subdir_name)
    if not os.path.exists(subdir_path):
        os.makedirs(subdir_path)
    return subdir_path


def get_filepath(file_directory, file_name, file_type):
    return "%s/%s.%s" % (file_directory, file_name, file_type)


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
    print("Saved to:", filepath, "\n")
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
    print("Saved to:", filepath, "\n")
    return filepath


def write_file(filepath, statements):
    with open(filepath, 'w') as file:
        file.write("%s" % statements)
    file.close()
    print("Saved to:", filepath, "\n")
    return filepath


def get_metatile_id(metatile_to_find, metatile_id_map):
    from model.metatile import Metatile
    for metatile_str, metatile_id in metatile_id_map.items():
        if Metatile.from_str(metatile_str) == metatile_to_find:
            return metatile_id
    return None


def metatile_coord_from_state_coord(state_coord, half_player_w, half_player_h, tile_dim):
    return (state_coord[0] - half_player_w) - (state_coord[0] - half_player_w) % tile_dim, \
           (state_coord[1] - half_player_h) - (state_coord[1] - half_player_h) % tile_dim


def state_in_metatile(metatile_coord, state_coord, half_player_w, half_player_h, tile_dim):
    return metatile_coord == metatile_coord_from_state_coord(state_coord, half_player_w, half_player_h, tile_dim)


def get_node_xy(node):
    state_dict = eval(node)
    return state_dict['x'], state_dict['y']


def get_node_at_coord(graph, coord):
    for node in graph.nodes():
        if get_node_xy(node) == coord:
            return node
    return None


def shortest_path_xy(state_graph, src_node, dest_node):
    shortest_path = nx.shortest_path(state_graph, src_node, dest_node)
    return [get_node_xy(node) for node in shortest_path]

# def state_coord_from_node(state_node):
#     state_dict = eval(state_node)
#     return state_dict['x'], state_dict['y']
#
#
# # return edges where the dest node is outside of the start node's metatile
# def get_edges_with_external_links(metatile_graph, half_player_w=20, half_player_h=20, tile_dim=40):
#
#     external_edges = []
#     for edge in metatile_graph.edges():
#         src_node = edge[0]
#         src_state_coord = state_coord_from_node(src_node)
#         dest_node = edge[1]
#         dest_state_coord = state_coord_from_node(dest_node)
#
#         src_metatile_coord = metatile_coord_from_state_coord(src_state_coord, half_player_w, half_player_h, tile_dim)
#
#         if not state_in_metatile(src_metatile_coord, dest_state_coord, half_player_w, half_player_h, tile_dim):
#             external_edges.append(edge)
#
#     return external_edges
