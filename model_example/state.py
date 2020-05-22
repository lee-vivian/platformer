"""
Player State Object
"""
from model.level import TILE_DIM


class StateExample:
    def __init__(self, x, y, is_start, goal_reached):
        self.x = x  # x coord of center of player
        self.y = y  # y coord of center of player
        self.is_start = is_start
        self.goal_reached = goal_reached

    def clone(self):
        return StateExample(self.x, self.y, self.is_start, self.goal_reached)

    def to_str(self):
        string = "{"
        string += "'x': " + str(self.x) + ", "
        string += "'y': " + str(self.y) + ", "
        string += "'is_start': " + str(self.is_start) + ", "
        string += "'goal_reached': " + str(self.goal_reached)
        string += "}"
        return string

    @staticmethod
    def from_str(string):
        state_dict = eval(string)
        return StateExample(state_dict['x'], state_dict['y'], state_dict['is_start'], state_dict['goal_reached'])

    def to_prolog_contents(self):
        prolog_contents = [
            "%d+TX*%d" % (self.x, TILE_DIM),
            "%d+TY*%d" % (self.y, TILE_DIM),
            "%d" % self.is_start,
            "%d" % self.goal_reached
        ]
        return ','.join(prolog_contents)

    @staticmethod
    def generic_prolog_contents(index=None):
        generic_prolog_contents = [
            "X", "Y", "IS", "GR"
        ]
        index_str = "" if index is None else str(index)
        generic_prolog_contents = [item + index_str for item in generic_prolog_contents]
        return ','.join(generic_prolog_contents)
