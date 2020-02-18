"""
Player State Object
"""


class State:
    def __init__(self, cur_x, cur_y, movex, movey, facing_right):
        self.x = cur_x
        self.y = cur_y
        self.movex = movex
        self.movey = movey
        self.facing_right = facing_right
