'''
Grid Cell Object for a Level (one of: [tile, blank])
'''

import networkx as nx

TILE = 40


class GridCell:
    def __init__(self, filled, graph):
        self.filled = filled
        self.graph = graph

    @staticmethod
    def node_at_coord(node, coord):
        state_dict = eval(node)
        return state_dict['x'] == coord[0] and state_dict['y'] == coord[1]

    @staticmethod
    def extract_grid_cells(level, graph):

        grid_cells = []
        tile_coords = level.get_border_coords(TILE) + level.get_platform_coords()

        for coord in level.get_all_possible_coords(TILE):

            filled = coord in tile_coords
            cell_graph = nx.DiGraph()

            for node in graph.nodes():
                if GridCell.node_at_coord(node, coord):
                    edges_at_node = graph.edges(node)
                    cell_graph.add_edges_from(edges_at_node)  # adds node, edges, and neighbor nodes

            # @TODO normalize x,y to cell_coord

            grid_cells.append(GridCell(filled, cell_graph))

        return grid_cells










