"""
Dump info about the precomputed state graph.
"""

# Note: use pypy3 to run; use pip_pypy3 to install third-party packages (e.g. networkx)

import networkx as nx
import argparse


def main(state_graph_file, dot):

    # Load in state graph
    state_graph = nx.read_gpickle(state_graph_file)

    if dot:
        print('digraph G {')
        print('  node [ shape="circle" fixedsize="true" width="1" ];')

        nodeids = {}
        for nodei, node in enumerate(state_graph.nodes):
            nodeid = 'n%d' % nodei
            nodeids[node] = nodeid

            nodedata = eval(node)
            nodeattr = ''
            if 'movex' in nodedata:
                nodeattr += ' pos="%f,%f!"' % (nodedata['x'] / 1.5 + nodedata['movex'] / 6.0, nodedata['y'] / -3.0 + nodedata['movey'] / -8.0)
                nodeattr += ' label="%d,%d;%d,%d"' % (nodedata['x'], nodedata['y'], nodedata['movex'], nodedata['movey'])
            else:
                nodeattr += ' pos="%f,%f!"' % (nodedata['x'] / 4, nodedata['y'] / -4)
                nodeattr += ' label="%d,%d"' % (nodedata['x'], nodedata['y'])

            if 'is_dead' in nodedata and nodedata['is_dead']:
                nodeattr += ' style="filled" fillcolor="red"'
            elif 'is_start' in nodedata and nodedata['is_start']:
                nodeattr += ' style="filled" fillcolor="blue"'
            elif 'goal_reached' in nodedata and nodedata['goal_reached']:
                nodeattr += ' style="filled" fillcolor="green"'
            elif 'onground' in nodedata and nodedata['onground']:
                nodeattr += ' style="filled" fillcolor="lightgray"'

            print('  %s [%s ];' % (nodeid, nodeattr))

        for edge in state_graph.edges:
            nodeid0 = nodeids[edge[0]]
            nodeid1 = nodeids[edge[1]]
            print('  %s -> %s;' % (nodeid0, nodeid1))

        print('}')

    else:
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
    parser.add_argument('--dot', const=True, nargs='?', type=bool, help="Output in dot format", default=False)
    args = parser.parse_args()

    main(args.state_graph_file, args.dot)
