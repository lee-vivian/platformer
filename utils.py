import os
import json
import pickle


def error_exit(msg):
    print(msg)
    exit(0)


def check_path_exists(filepath):
    if not os.path.exists(filepath):
        error_exit("Missing file: %s" % filepath)


def get_save_directory(level_saved_files_dir, new_dir):
    if not os.path.exists(level_saved_files_dir):
        os.makedirs(level_saved_files_dir)

    new_dir_path = "%s/%s" % (level_saved_files_dir, new_dir)
    if not os.path.exists(new_dir_path):
        os.makedirs(new_dir_path)

    return new_dir_path


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
