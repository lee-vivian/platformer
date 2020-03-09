'''
Metatile Object that describes each grid cell in a Level
'''

import networkx as nx
import pickle

from model.level import TILE_DIM


def read_pickle(filepath):
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


class Metatile:
    def __init__(self, filled, graph_as_dict):
        self.filled = filled
        self.graph_as_dict = graph_as_dict

    def __eq__(self, other):
        if isinstance(other, Metatile):
            return self.filled == other.filled and self.graph_as_dict == other.graph_as_dict
        return False

    def to_str(self):
        string = "{'filled': "
        string += "1" if self.filled else "0"
        string += ", 'graph': "
        string += str(self.graph_as_dict)
        string += "}"
        return string

    @staticmethod
    def from_str(string):
        metatile_dict = eval(string)
        return Metatile(metatile_dict['filled'], metatile_dict['graph'])

    @staticmethod
    def get_unique_metatiles(metatiles):
        unique_metatiles = []
        for metatile in metatiles:
            if metatile not in unique_metatiles:
                unique_metatiles.append(metatile)
        return unique_metatiles

    @staticmethod
    def get_unique_metatiles_for_level(game_name, level_name, player_img='block'):
        metatile_coords_dict_file = "level_saved_files_%s/metatile_coords_dicts/%s/%s.pickle" % \
                                    (player_img, game_name, level_name)
        metatile_coords_dict = read_pickle(metatile_coords_dict_file)
        metatiles = [Metatile.from_str(key) for key in metatile_coords_dict.keys()]
        return metatiles

    @staticmethod
    def get_unique_metatiles_for_levels(game_level_pairs, player_img='block'):
        combined_metatiles = []
        for game, level in game_level_pairs:
            combined_metatiles += Metatile.get_unique_metatiles_for_level(game, level, player_img)
        return Metatile.get_unique_metatiles(combined_metatiles)

    @staticmethod
    def get_coord_node_dict(graph):
        coord_node_dict = {}
        for node in graph.nodes():
            state_dict = eval(node)
            node_coord = (state_dict['x'], state_dict['y'])

            if coord_node_dict.get(node_coord) is None:
                coord_node_dict[node_coord] = [node]
            else:
                coord_node_dict[node_coord].append(node)

        return coord_node_dict

    @staticmethod
    def get_node_spatial_hash(graph, all_possible_coords):

        coord_node_dict = Metatile.get_coord_node_dict(graph)
        spatial_hash = {}

        for metatile_coord in all_possible_coords:
            spatial_hash[metatile_coord] = []

            for x in range(metatile_coord[0], metatile_coord[0] + TILE_DIM):
                for y in range(metatile_coord[1], metatile_coord[1] + TILE_DIM):
                    temp_coord = (x, y)
                    if coord_node_dict.get(temp_coord) is not None:
                        spatial_hash[metatile_coord] += coord_node_dict[temp_coord]

        return spatial_hash  # {metatile coord: nodes (states) at coord}

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
    def extract_metatiles(level, graph, metatile_coords_dict_file, coord_metatile_dict_file):

        all_metatiles = []
        unique_metatiles = []
        metatile_str_metatile_dict = {}
        metatile_coords_dict = {}
        coord_metatile_dict = {}

        tile_coords = level.platform_coords + level.goal_coords
        tile_coords_dict = {}
        for coord in tile_coords:
            tile_coords_dict[coord] = 1

        all_possible_coords = level.get_all_possible_coords()
        node_spatial_hash = Metatile.get_node_spatial_hash(graph, all_possible_coords)  # {metatile coord: nodes (states) at coord}

        for metatile_coord in all_possible_coords:

            filled = tile_coords_dict.get(metatile_coord) is not None
            metatile_graph = nx.DiGraph()

            nodes_in_metatile = node_spatial_hash.get(metatile_coord)
            if len(nodes_in_metatile) > 0:
                for node in nodes_in_metatile:
                    subgraph = graph.edge_subgraph(graph.edges(node)).copy()
                    metatile_graph = nx.compose(metatile_graph, subgraph)  # join graphs

                metatile_graph = Metatile.get_normalized_graph(metatile_graph, metatile_coord)  # normalize graph nodes to coord

            metatile_graph_as_dict = nx.to_dict_of_dicts(metatile_graph)

            new_metatile = Metatile(filled, metatile_graph_as_dict)
            all_metatiles.append(new_metatile)

            # Get standardized string of new metatile
            new_metatile_str = new_metatile.to_str()

            if new_metatile not in unique_metatiles:  # have not seen this metatile yet, add to dict
                unique_metatiles.append(new_metatile)
                metatile_str_metatile_dict[new_metatile_str] = new_metatile

            for key, value in metatile_str_metatile_dict.items():  # get standardized string of new_metatile
                if value == new_metatile:
                    new_metatile_str = key
                    break

            # Construct {metatile: coords} dict
            if metatile_coords_dict.get(new_metatile_str) is None:
                metatile_coords_dict[new_metatile_str] = [metatile_coord]
            else:
                metatile_coords_dict[new_metatile_str].append(metatile_coord)

            # Construct {coord: metatile} dict
            coord_metatile_dict[metatile_coord] = new_metatile_str

        # Save coord_metatile_dict
        write_pickle(coord_metatile_dict_file, coord_metatile_dict)

        # Save metatile_coords_dict
        write_pickle(metatile_coords_dict_file, metatile_coords_dict)

        return all_metatiles



