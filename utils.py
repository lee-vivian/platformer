import os
import json
import pickle


def error_exit(msg):
    print(msg)
    exit(0)


def check_path_exists(filepath):
    if not os.path.exists(filepath):
        error_exit("Missing file: %s" % filepath)


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


def metatile_coord_from_state_coord(state_coord, half_player_w, half_player_h, tile_dim):
    return (state_coord[0] - half_player_w) - (state_coord[0] - half_player_w) % tile_dim, \
           (state_coord[1] - half_player_h) - (state_coord[1] - half_player_h) % tile_dim


def state_in_metatile(metatile_coord, state_coord, half_player_w, half_player_h, tile_dim):
    return metatile_coord == metatile_coord_from_state_coord(state_coord, half_player_w, half_player_h, tile_dim)
