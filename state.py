"""
Player State Object
"""

class State:
    def __init__(self, x, y, movex, movey, facing_right, onground, goal_reached):
        self.x = x  # x coord of center of player
        self.y = y  # y coord of center of player
        self.movex = movex
        self.movey = movey
        self.facing_right = facing_right
        self.onground = onground
        self.goal_reached = goal_reached

    def clone(self):
        return State(self.x, self.y, self.movex, self.movey, self.facing_right, self.onground, self.goal_reached)

    def to_str(self):
        string = "{"
        string += "'x': " + str(self.x) + ", "
        string += "'y': " + str(self.y) + ", "
        string += "'movex': " + str(self.movex) + ", "
        string += "'movey': " + str(self.movey) + ", "
        string += "'facing_right': " + str(self.facing_right) + ", "
        string += "'onground': " + str(self.onground) + ", "
        string += "'goal_reached': " + str(self.goal_reached)
        string += "}"
        return string
