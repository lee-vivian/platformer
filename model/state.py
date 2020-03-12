"""
Player State Object
"""


class State:
    def __init__(self, x, y, movex, movey, facing_right, onground, is_start, goal_reached):
        self.x = x  # x coord of center of player
        self.y = y  # y coord of center of player
        self.movex = movex
        self.movey = movey
        self.facing_right = facing_right
        self.onground = onground
        self.is_start = is_start
        self.goal_reached = goal_reached

    def clone(self):
        return State(self.x, self.y, self.movex, self.movey, self.facing_right, self.onground, self.is_start, self.goal_reached)

    def to_str(self):
        string = "{"
        string += "'x': " + str(self.x) + ", "
        string += "'y': " + str(self.y) + ", "
        string += "'movex': " + str(self.movex) + ", "
        string += "'movey': " + str(self.movey) + ", "
        string += "'facing_right': " + str(self.facing_right) + ", "
        string += "'onground': " + str(self.onground) + ", "
        string += "'is_start': " + str(self.is_start) + ", "
        string += "'goal_reached': " + str(self.goal_reached)
        string += "}"
        return string

    @staticmethod
    def from_str(string):
        state_dict = eval(string)
        return State(state_dict['x'], state_dict['y'], state_dict['movex'], state_dict['movey'],
                     state_dict['facing_right'], state_dict['onground'], state_dict['is_start'],
                     state_dict['goal_reached'])

