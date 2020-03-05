'''
Get the shortest path from start to goal in a level
'''

import os
import networkx as nx
import json
import datetime

from model.player import Player


PLAYER_IMG = 'block'
LEVEL_SAVED_FILES_DIR = "level_saved_files_" + PLAYER_IMG + "/"
player = Player(PLAYER_IMG)


def get_game_shortest_path_dir(game):
    shortest_path_dir = LEVEL_SAVED_FILES_DIR + "shortest_paths/"
    game_shortest_path_dir = shortest_path_dir + game + "/"
    saved_file_directories = [shortest_path_dir, game_shortest_path_dir]
    for directory in saved_file_directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
    return game_shortest_path_dir


def get_state_graph(game, level):
    game_enumerated_state_graph_dir = LEVEL_SAVED_FILES_DIR + "enumerated_state_graphs/" + game + "/"
    state_graph_filepath = game_enumerated_state_graph_dir + level + ".gpickle"
    if not os.path.exists(state_graph_filepath):
        print("Error: Enumerated state graph for (%s: level %s) does not exist" % (game, level))
        exit(0)
    state_graph = nx.read_gpickle(state_graph_filepath)
    return state_graph


def get_goal_tile_coords(game, level):
    goal_tile_coords = []
    all_levels_info_file = LEVEL_SAVED_FILES_DIR + "all_levels_info.json"
    with open(all_levels_info_file, 'r') as f:
        all_levels_info = json.load(f)
    contents = all_levels_info["contents"]
    for level_info in contents:
        if level_info['game_name'] == game and level_info['level_name'] == level:
            goal_tile_coords += eval(level_info['goal_coords'])
            break
    return goal_tile_coords


def get_goal_node(game, level, state_graph):

    # Get goal coords for level
    goal_coords = get_goal_tile_coords(game, level)
    if len(goal_coords) == 0:
        print("Error: There are no goal tiles in (%s: level %s)" % (game, level))
        exit(0)

    # Return first node in state_graph where player collides with a goal tile
    for node in state_graph.nodes:
        state_dict = eval(node)
        if player.collide(state_dict['x'], state_dict['y'], goal_coords):
            return node

    return None


def main(game, level):

    print("Started get_shortest_path for (%s: level %s) ..." % (game, level))

    start_time = datetime.datetime.now()
    state_graph = get_state_graph(game, level)
    print("Retrieved state graph")
    source_node = player.start_state().to_str()
    target_node = get_goal_node(game, level, state_graph)
    print("Retrieved start and target nodes")

    if target_node is None:  # player never collided with a goal tile in the enumerated state graph
        print("Error: No path exists between the source and target nodes")
        exit(0)
    else:
        print("Finding shortest path for (%s: level %s) ..." % (game, level))
        shortest_path = nx.shortest_path(state_graph, source_node, target_node)
        game_shortest_path_dir = get_game_shortest_path_dir(game)
        shortest_path_filepath = game_shortest_path_dir + level + ".txt"
        with open(shortest_path_filepath, 'w') as f:
            f.write(str(shortest_path))
        f.close()
        print("Saved to:", shortest_path_filepath)

    end_time = datetime.datetime.now()
    print("Runtime:", str(end_time-start_time))


if __name__ == "__main__":

    GAME_LEVEL_PAIRS = [
        ('sample', 'sample_hallway'),
        ('super_mario_bros', 'mario-1-1'),
        ('super_mario_bros', 'mario-2-1'),
        ('kid_icarus', 'kidicarus_1')
    ]

    for game, level in GAME_LEVEL_PAIRS:
        main(game, level)






