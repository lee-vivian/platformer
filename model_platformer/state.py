"""
Player State Object
"""
from model.level import TILE_DIM


class StatePlatformer:
    def __init__(self, x, y, movex, movey, onground, is_start, goal_reached, hit_bonus_coord, is_dead):
        self.x = x  # x coord of center of player
        self.y = y  # y coord of center of player
        self.movex = movex
        self.movey = movey
        self.onground = onground
        self.is_start = is_start
        self.goal_reached = goal_reached
        self.hit_bonus_coord = hit_bonus_coord
        self.is_dead = is_dead

    def clone(self):
        return StatePlatformer(self.x, self.y, self.movex, self.movey, self.onground, self.is_start, self.goal_reached,
                               self.hit_bonus_coord, self.is_dead)

    def to_str(self):
        string = "{"
        string += "'x': " + str(self.x) + ", "
        string += "'y': " + str(self.y) + ", "
        string += "'movex': " + str(self.movex) + ", "
        string += "'movey': " + str(self.movey) + ", "
        string += "'onground': " + str(self.onground) + ", "
        string += "'is_start': " + str(self.is_start) + ", "
        string += "'goal_reached': " + str(self.goal_reached) + ", "
        string += "'hit_bonus_coord': '" + str(self.hit_bonus_coord) + "', "
        string += "'is_dead': " + str(self.is_dead)
        string += "}"
        return string

    @staticmethod
    def from_str(string):
        state_dict = eval(string)
        return StatePlatformer(state_dict['x'], state_dict['y'], state_dict['movex'], state_dict['movey'],
                               state_dict['onground'], state_dict['is_start'], state_dict['goal_reached'],
                               state_dict['hit_bonus_coord'], state_dict['is_dead'])

    def to_prolog_contents(self):
        prolog_contents = [
            "%d+TX*%d" % (self.x, TILE_DIM),
            "%d+TY*%d" % (self.y, TILE_DIM),
            "%d" % self.movex,
            "%d" % self.movey,
            "%d" % self.onground,
            "%d" % self.is_start,
            "%d" % self.goal_reached,
            "\"%s\"" % self.hit_bonus_coord,
            "%d" % self.is_dead
        ]
        return ','.join(prolog_contents)

    @staticmethod
    def generic_prolog_contents(index=None):
        generic_prolog_contents = [
            "X", "Y", "MX", "MY", "OG", "IS", "GR", "HBC", "ID"
        ]
        index_str = "" if index is None else str(index)
        generic_prolog_contents = [item + index_str for item in generic_prolog_contents]
        return ','.join(generic_prolog_contents)

    @staticmethod
    def generic_bonus_reachability_expression():
        return "HBC != \"\""

    @staticmethod
    def generic_ground_reachability_expression():
        return "OG == 1"

    @staticmethod
    def generic_start_reachability_expression():
        return "IS == 1"

    @staticmethod
    def generic_goal_reachability_expression():
        return "GR == 1"

    @staticmethod
    def prolog_state_contents_x_index():
        generic_prolog_contents = StatePlatformer.generic_prolog_contents().split(',')
        return generic_prolog_contents.index('X')

    @staticmethod
    def prolog_state_contents_y_index():
        generic_prolog_contents = StatePlatformer.generic_prolog_contents().split(',')
        return generic_prolog_contents.index('Y')

    @staticmethod
    def prolog_state_contents_is_start_index():
        generic_prolog_contents = StatePlatformer.generic_prolog_contents().split(',')
        return generic_prolog_contents.index('IS')

    @staticmethod
    def prolog_state_contents_goal_reached_index():
        generic_prolog_contents = StatePlatformer.generic_prolog_contents().split(',')
        return generic_prolog_contents.index('GR')

    @staticmethod
    def prolog_state_contents_on_ground_index():
        generic_prolog_contents = StatePlatformer.generic_prolog_contents().split(',')
        return generic_prolog_contents.index('OG')

    @staticmethod
    def prolog_state_contents_hit_bonus_coord_index():
        generic_prolog_contents = StatePlatformer.generic_prolog_contents().split(',')
        return generic_prolog_contents.index('HBC')

