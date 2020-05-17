"""
Player Action Object
"""


class ActionExample:
    NONE = 'X'
    UP = 'U'
    DOWN = 'D'
    LEFT = 'L'
    RIGHT = 'R'
    
    def __init__(self, direction):
        self.direction = direction

    def to_str(self):
        return self.direction

    @staticmethod
    def allActions():
        action_set = []
        for direction in [ActionExample.NONE, ActionExample.UP, ActionExample.DOWN, ActionExample.LEFT, ActionExample.RIGHT]:
            action_set.append(ActionExample(direction))
        return action_set
