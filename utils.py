import os
import json
import pickle
from math import sqrt, pow
import re
import networkx as nx


def error_exit(msg):
    print("ERROR: %s" % msg)
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
    dir = get_directory(directory) if directory != "" else ""
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


def read_txt(filepath):
    with open(filepath, encoding='utf-8', errors='ignore') as file:
        content = file.read()
        return content


def write_file(filepath, statements):
    with open(filepath, 'w') as file:
        file.write("%s" % statements)
    file.close()
    print("Saved to: %s\n" % filepath)
    return filepath


def all_equal(list):
    return all(i == list[0] for i in list)


def list_to_dict(list):
    dictionary = {}
    for item in list:
        dictionary[item] = 1
    return dictionary


def get_unique_lines(lines_str):
    unique_str_dict = {}
    parts = lines_str.split("\n")
    for part in parts:
        unique_str_dict[part] = 1
    unique_lines_str = "\n".join(unique_str_dict.keys())
    return unique_lines_str


def remove_duplicate_lines_from_file(filepath):
    all_lines_str = ""
    all_lines_count = 0
    f = open(filepath, 'r')
    for line in f:
        all_lines_str += line
        all_lines_count += 1
    unique_lines_str = get_unique_lines(all_lines_str)
    write_file(filepath, unique_lines_str)

    print("Filepath: %s" % filepath)
    print("Lines before: %d" % all_lines_count)
    print("Lines after: %d" % len(unique_lines_str.split("\n")))


def euclidean_distance(coord_a, coord_b):
    x1, y1 = coord_a
    x2, y2 = coord_b
    return int(sqrt(pow(x1-x2, 2) + pow(y1-y2, 2)))


def get_all_indices(item, list):
    return [i for i, x in enumerate(list) if x == item]


def get_basepath_filename(filepath, extension):
    filename = os.path.basename(filepath)
    filename = re.match(r'([.a-zA-Z0-9_-]+).%s' % extension, filename)
    filename = filename.group(1)
    return filename


def merge_level_txt_files(files, savefile):
    count = 0
    with open(savefile, 'w') as outfile:
        for file in files:
            if os.path.exists(file):
                count += 1
                with open(file, 'r') as infile:
                    outfile.write("Level: %s\n" % file)
                    for line in infile:
                        outfile.write(line)
                    outfile.write("\n\n")
        outfile.write("\nCombined Levels: %d\n" % count)
    print("Saved to: %s" % savefile)


def create_generated_level_path_txt(generated_levels):
    generated_level_file_format = 'level_structural_layers/generated/%s.txt'
    generated_paths_file_format = 'level_saved_files_block/generated_level_paths/%s.pickle'
    for level in generated_levels:
        outfile = "path_%s.txt" % level
        generated_level_txt = read_txt(generated_level_file_format % level)
        generated_path_coords = read_pickle(generated_paths_file_format % level)

        contents = "----- Level: %s -----\n\n" % level
        contents += "----- Structure -----\n"
        contents += generated_level_txt + "\n"
        contents += "----- Solution Path State Coords -----\n"
        contents += " => ".join(generated_path_coords)

        write_file(outfile, contents)


def shortest_path_xy(state_graph):

    def get_node_xy(node):
        state_dict = eval(node)
        return state_dict['x'], state_dict['y']

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

    start_states, goal_states = get_start_and_goal_states(state_graph)

    if len(start_states) < 1:
        error_exit("No start states found in state graph")

    if len(goal_states) < 1:
        error_exit("No goal states found in state graph")

    for src in start_states:
        for dest in goal_states:
            if nx.has_path(state_graph, src, dest):
                shortest_path = nx.dijkstra_path(state_graph, src, dest, weight='weight')
                return {
                    "path_coords": [get_node_xy(node) for node in shortest_path],
                    "start_coord": get_node_xy(src),
                    "goal_coord": get_node_xy(dest)
                }

    error_exit("No solution path found in state graph")
