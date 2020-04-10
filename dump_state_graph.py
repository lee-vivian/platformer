"""
Dump info about the precomputed state graph.
"""

# Note: use pypy3 to run; use pip_pypy3 to install third-party packages (e.g. networkx)

import networkx as nx
import argparse


def main(state_graph_file):

    # Load in state graph
    state_graph = nx.read_gpickle(state_graph_file)

    # Print
    for node in state_graph.nodes:
        print(node)

    for node in state_graph.nodes:
        print()
        print(node)
        for edge in state_graph.out_edges(node):
            print(' ' * 10, '->', ','.join(state_graph.edges[edge]["action"]), '->', edge[1])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Print state graph')
    parser.add_argument('state_graph_file', type=str, help="File path of the state graph to print")
    args = parser.parse_args()

    main(args.state_graph_file)
