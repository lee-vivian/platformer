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
    def get_node_spatial_hash(graph):

        spatial_hash = {}

        for node in graph.nodes():

            state_dict = eval(node)
            coord = (state_dict['x'], state_dict['y'])

            if spatial_hash.get(coord) is None:
                spatial_hash[coord] = [node]
            else:
                spatial_hash[coord].append(node)

        return spatial_hash

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
        metatiles_dict = {}

        tile_coords = level.get_border_coords(TILE) + level.get_platform_coords() + level.get_goal_coords()
        tile_coords_dict = {}
        for coord in tile_coords:
            tile_coords_dict[coord] = 1

        node_spatial_hash = Metatile.get_node_spatial_hash(graph)

        for coord in level.get_all_possible_coords(TILE):

            filled = tile_coords_dict.get(coord) is not None
            metatile_graph = nx.DiGraph()

            nodes_at_coord = node_spatial_hash.get(coord)

            if nodes_at_coord is not None:
                for node in nodes_at_coord:
                    subgraph = graph.edge_subgraph(graph.edges(node)).copy()
                    metatile_graph = nx.compose(metatile_graph, subgraph)  # join graphs

                metatile_graph = Metatile.get_normalized_graph(metatile_graph, coord)  # normalize graph to coord

            metatile_graph_as_dict = nx.to_dict_of_dicts(metatile_graph)
            metatile = Metatile(filled, metatile_graph_as_dict)

            metatiles.append(metatile)

            if metatiles_dict.get(coord) is None:
                metatiles_dict[coord] = [metatile]
            else:
                metatiles_dict[coord].append(metatile)

        return metatiles

