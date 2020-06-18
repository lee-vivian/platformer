"""
Metatile Object that describes each grid cell in a Level
"""

import networkx as nx

from utils import error_exit, read_pickle, get_filepath

METATILE_TYPES = ["start", "goal", "block", "bonus", "empty", "one_way_platform", "hazard", "wall", "permeable_wall"]


class Metatile:
    def __init__(self, type, graph_as_dict, games=None, levels=None):
        if type not in METATILE_TYPES:
            error_exit("Given metatile type [%s] must be one of %s" % (type, str(METATILE_TYPES)))
        self.type = type
        self.graph_as_dict = graph_as_dict
        self.games = [] if games is None else games
        self.levels = [] if levels is None else levels

    def __eq__(self, other):
        if isinstance(other, Metatile):
            return self.type == other.type and self.graph_as_dict == other.graph_as_dict
        return False

    def get_games(self):
        return self.games.copy()

    def get_levels(self):
        return self.levels.copy()

    def merge_games_and_levels(self, other):
        if not self == other:
            error_exit("Cannot merge metatiles that have different types or graphs")
        combined_games = list(set(self.get_games() + other.get_games()))
        combined_levels = list(set(self.get_levels() + other.get_levels()))
        return Metatile(self.type, self.graph_as_dict, games=combined_games, levels=combined_levels)

    def to_str(self):
        graph = str(self.graph_as_dict)
        return "{'type': '%s', 'graph': %s, 'games': %s, 'levels': %s}" % (self.type, graph, str(self.games), str(self.levels))

    @staticmethod
    def from_str(string):
        metatile_dict = eval(string)
        return Metatile(metatile_dict['type'], metatile_dict['graph'], metatile_dict['games'], metatile_dict['levels'])

    @staticmethod
    def get_metatile_coord_from_state_coord(state_coord, tile_dim):
        metatile_x = int(state_coord[0] / tile_dim) * tile_dim
        metatile_y = int(state_coord[1] / tile_dim) * tile_dim
        return metatile_x, metatile_y

    @staticmethod
    def get_unique_metatiles(metatiles):
        unique_metatiles = []
        for metatile in metatiles:
            if metatile not in unique_metatiles:
                unique_metatiles.append(metatile)
        return unique_metatiles

    @staticmethod
    def get_unique_metatiles_for_level(level, player_img):
        unique_metatiles_dir = "level_saved_files_%s/unique_metatiles" % player_img
        unique_metatiles_file = get_filepath(unique_metatiles_dir, "%s.pickle" % level)
        unique_metatiles = read_pickle(unique_metatiles_file)
        return unique_metatiles

    @staticmethod
    def get_unique_metatiles_for_levels(levels, player_img):
        combined_metatiles = []
        for level in levels:
            combined_metatiles += Metatile.get_unique_metatiles_for_level(level, player_img)
        return Metatile.get_unique_metatiles(combined_metatiles)

    @staticmethod
    def get_normalized_graph(graph, coord, normalize=True):

        normalized_graph = nx.DiGraph()
        edge_attr_dict = nx.get_edge_attributes(graph, "action")
        x, y = coord[0], coord[1]

        if not normalize:  # add coord to state x,y if un-normalizing graph
            x *= -1
            y *= -1

        for edge in edge_attr_dict.keys():
            source_dict = eval(edge[0])
            source_dict['x'] -= x
            source_dict['y'] -= y
            source_node = str(source_dict)

            dest_dict = eval(edge[1])
            dest_dict['x'] -= x
            dest_dict['y'] -= y
            dest_node = str(dest_dict)

            normalized_graph.add_edge(source_node, dest_node, action=edge_attr_dict[edge])

        return normalized_graph
