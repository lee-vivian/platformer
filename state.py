"""
Player State Object
"""


class State:
    def __init__(self, cur_x, cur_y, movex, onground):
        self.x = cur_x
        self.y = cur_y
        self.movex = movex
        self.onground = onground
