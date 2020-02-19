"""
Player State Object
"""


class State:
    def __init__(self, x, y, movex, movey, facing_right, onground, goal_reached):
        self.x = x
        self.y = y
        self.movex = movex
        self.movey = movey
        self.facing_right = facing_right
        self.onground = onground
        self.goal_reached = goal_reached

    def clone(self):
        return State(self.x, self.y, self.movex, self.movey, self.facing_right, self.onground, self.goal_reached)

    def to_str(self):
        string = ""
        string += "(" + str(self.x) + ", " + str(self.y) + ") | "
        string += "[" + str(self.movex) + ", " + str(self.movey) + "] | "
        string += "right | " if self.facing_right else "left | "
        string += "ground | " if self.onground else "fall | "
        string += "done" if self.goal_reached else "ip"
        return string
