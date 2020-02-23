'''
Grid Cell Object for a Level (one of: [tile, blank])
'''

import networkx as nx

TILE = 40


class GridCell:
    def __init__(self, filled, graph):
        self.filled = filled
        self.graph = graph

    def to_str(self):
        string = "{filled: "
        string += "1" if self.filled else "0"
        string += ", edges: ["
        for edge in self.graph.edges():
            string += str(edge) + ", "
        string = string[0:len(string)-len(", ")]
        string += "]}"
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
    def extract_grid_cells(level, graph):

        grid_cells = []
        tile_coords = level.get_border_coords(TILE) + level.get_platform_coords()

        for coord in level.get_all_possible_coords(TILE):

            filled = coord in tile_coords  # blank or tile
            cell_graph = nx.DiGraph()

            for node in graph.nodes():
                if GridCell.node_at_coord(node, coord):
                    subgraph = graph.edge_subgraph(graph.edges(node)).copy()
                    cell_graph = nx.compose(cell_graph, subgraph)  # adds node, neighbor nodes, edges, and edge attrs

            normalized_cell_graph = GridCell.get_normalized_graph(cell_graph, coord)  # normalize grid cell to coord
            grid_cells.append(GridCell(filled, normalized_cell_graph))

        return grid_cells










