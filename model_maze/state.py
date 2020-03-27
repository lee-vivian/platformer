"""
Player State Object
"""


class StateMaze:
    def __init__(self, x, y, is_start, goal_reached):
        self.x = x  # x coord of center of player
        self.y = y  # y coord of center of player
        self.is_start = is_start
        self.goal_reached = goal_reached

    def clone(self):
        return StateMaze(self.x, self.y, self.is_start, self.goal_reached)

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
        return StateMaze(state_dict['x'], state_dict['y'], state_dict['is_start'], state_dict['goal_reached'])
