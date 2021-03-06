"""
Enumerate the state space of a level
"""

# Note: use pypy3 to run; use pip_pypy3 to install third-party packages (e.g. networkx)

import os
import networkx as nx
import re
import datetime
import argparse

from model.level import Level
from utils import get_filepath, euclidean_distance

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
    game_state_graph_directory = "level_saved_files_%s/enumerated_state_graphs/%s" % (player_img, game_name)
    save_filename = "%s.gpickle" % level_name
    state_graph_file = get_filepath(game_state_graph_directory, save_filename)
    return state_graph_file


def parse_state_graph_filename(state_graph_file):
    match = re.match(r'level_saved_files_[^/]+/enumerated_state_graphs/([^/]+)/([a-zA-Z0-9_-]+).gpickle', state_graph_file)
    game = match.group(1)
    level = match.group(2)
    return {
        "game": game,
        "level": level
    }


def get_action_set():
    return Action.allActions()


def enumerate_states(player_model, start_state, graph, action_set):
    start_state_str = start_state.to_str()
    graph.add_node(start_state_str)

    unexplored_states = set([start_state_str])
    explored_states = set()

    while len(unexplored_states) > 0:
        cur_state_str = unexplored_states.pop()
        explored_states.add(cur_state_str)

        cur_state = State.from_str(cur_state_str)

        for action in action_set:
            next_state = player_model.next_state(state=cur_state, action=action)
            next_state_str = next_state.to_str()
            if next_state_str not in explored_states and next_state_str not in unexplored_states:
                graph.add_node(next_state_str)
                unexplored_states.add(next_state_str)

            if not graph.has_edge(cur_state_str, next_state_str):
                distance = euclidean_distance((cur_state.x, cur_state.y), (next_state.x, next_state.y))
                graph.add_edge(cur_state_str, next_state_str, weight=distance, action=[action.to_str()])
            else:
                graph.get_edge_data(cur_state_str, next_state_str)["action"].append(action.to_str())

    print('graph size:', len(graph.nodes), len(graph.edges))
    return graph


def build_state_graph(player_img, level_obj, state_graph_file):
    player_model = Player(player_img, level_obj)
    start_state = player_model.get_start_state()
    action_set = get_action_set()
    state_graph = enumerate_states(player_model=player_model, start_state=start_state, graph=nx.DiGraph(),
                                   action_set=action_set)
    nx.write_gpickle(state_graph, state_graph_file)
    print("Saved to:", state_graph_file)


def main(game_name, level_name, player_img):

    start_time = datetime.datetime.now()
    print("\nEnumerating states for level: " + str(level_name) + " ...")

    level_obj = Level.generate_level_from_file(game_name, level_name)
    state_graph_file = get_state_graph_file(game_name, level_name, player_img)
    build_state_graph(player_img, level_obj, state_graph_file)

    end_time = datetime.datetime.now()
    runtime = str(end_time - start_time)
    print("Runtime: %s\n" % runtime)
    return state_graph_file, runtime


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Enumerate state graph for the given level')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    parser.add_argument('--player_img', type=str, help='Player image', default='block')
    args = parser.parse_args()

    main(args.game, args.level, args.player_img)
