'''
Enumerate the state space of a level
'''

# Note: use pypy3 to run; use pip_pypy3 to install third-party packages (e.g. networkx)

import os
import networkx as nx
import datetime
import argparse

from model.level import Level

# game specifics
if os.getenv('MAZE'):
    print('***** USING MAZE RULES *****')
    from model_maze.player import PlayerMaze as Player
    from model_maze.state import StateMaze as State
    from model_maze.action import ActionMaze as Action
else:
    print('***** USING PLATFORMER RULES *****')
    from model_platformer.player import PlayerPlatformer as Player
    from model_platformer.state import StatePlatformer as State
    from model_platformer.action import ActionPlatformer as Action



def get_state_graph_file(game_name, level_name, player_img):

    level_saved_files_dir = "level_saved_files_%s/" % player_img
    enumerated_state_graphs_dir = level_saved_files_dir + "enumerated_state_graphs/"
    game_enumerated_state_graphs_dir = enumerated_state_graphs_dir + game_name + "/"
    saved_files_directories = [level_saved_files_dir, enumerated_state_graphs_dir, game_enumerated_state_graphs_dir]

    for directory in saved_files_directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

    state_graph_file = game_enumerated_state_graphs_dir + str(level_name) + ".gpickle"
    return state_graph_file


def get_action_set():
    return Action.allActions()


def enumerate_states(player_model, start_state, graph, action_set, platform_coords, goal_coords):
    start_state_str = start_state.to_str()
    graph.add_node(start_state_str)

    unexplored_states = [start_state_str]
    explored_states = []

    while len(unexplored_states) > 0:

        cur_state_str = unexplored_states.pop(0)
        explored_states.append(cur_state_str)

        for action in action_set:
            cur_state = State.from_str(cur_state_str)
            next_state = player_model.next_state(cur_state, action, platform_coords, goal_coords)
            next_state_str = next_state.to_str()
            if next_state_str not in explored_states and next_state_str not in unexplored_states:
                graph.add_node(next_state_str)
                unexplored_states.append(next_state_str)
            if not graph.has_edge(cur_state_str, next_state_str):
                graph.add_edge(cur_state_str, next_state_str, action=[action.to_str()])
            else:
                graph.get_edge_data(cur_state_str, next_state_str)["action"].append(action.to_str())

    return graph


def build_state_graph(level, player_img, state_graph_file):
    player_model = Player(player_img, level.start_coord)
    start_state = player_model.start_state()
    action_set = get_action_set()
    state_graph = enumerate_states(player_model, start_state, nx.DiGraph(), action_set, level.platform_coords, level.goal_coords)
    nx.write_gpickle(state_graph, state_graph_file)
    print("Saved to:", state_graph_file)


def main(game_name, level_name, player_img):

    start_time = datetime.datetime.now()
    print("\nEnumerating states for level: " + str(level_name) + " ...")

    level = Level.generate_level_from_file(game_name, level_name)
    state_graph_file = get_state_graph_file(game_name, level_name, player_img)
    build_state_graph(level, player_img, state_graph_file)

    end_time = datetime.datetime.now()
    print("Runtime: ", end_time - start_time, "\n")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Enumerate state graph for the given level')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    args = parser.parse_args()

    main(args.game, args.level, args.player_img)
