'''
Metatile Object that describes each grid cell in a Level
'''

import networkx as nx

TILE = 40


class Metatile:
    def __init__(self, filled, graph_as_dict):
        self.filled = filled
        self.graph_as_dict = graph_as_dict

    def to_str(self):
        string = "{filled: "
        string += "1" if self.filled else "0"
        string += ", graph: "
        string += str(self.graph_as_dict)
        string += "}"
        return string

    @staticmethod
    def node_at_coord(node, coord):
        state_dict = eval(node)
        return state_dict['x'] == coord[0] and state_dict['y'] == coord[1]

    @staticmethod
    def get_normalized_graph(graph, coord):

        normalized_graph = nx.DiGraph()
        edge_attr_dict = nx.get_edge_attributes(graph, "action")

        for edge in edge_attr_dict.keys():
            source_dict = eval(edge[0])
            source_dict['x'] -= coord[0]
            source_dict['y'] -= coord[1]
            source_node = str(source_dict)

            dest_dict = eval(edge[1])
            dest_dict['x'] -= coord[0]
            dest_dict['y'] -= coord[1]
            dest_node = str(dest_dict)

            normalized_graph.add_edge(source_node, dest_node, action=edge_attr_dict[edge])

        return normalized_graph

    @staticmethod
    def extract_tiles(level, graph):

        metatiles = []
        tile_coords = level.get_border_coords(TILE) + level.get_platform_coords() + level.get_goal_coords()

        for coord in level.get_all_possible_coords(TILE):

            filled = coord in tile_coords  # False if blank, True if tile
            cell_graph = nx.DiGraph()

            for node in graph.nodes():
                if Metatile.node_at_coord(node, coord):
                    subgraph = graph.edge_subgraph(graph.edges(node)).copy()
                    cell_graph = nx.compose(cell_graph, subgraph)  # adds node, neighbor nodes, edges, and edge attrs

            normalized_cell_graph = Metatile.get_normalized_graph(cell_graph, coord)  # normalize grid cell to coord
            normalized_cell_graph_dict = nx.to_dict_of_dicts(normalized_cell_graph)
            metatiles.append(Metatile(filled, normalized_cell_graph_dict))

        return metatiles
