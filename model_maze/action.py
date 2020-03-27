"""
Player Action Object
"""


class ActionMaze:
    NONE = 'X'
    NORTH = 'N'
    SOUTH = 'S'
    EAST = 'E'
    WEST = 'W'
    
    def __init__(self, direction):
        self.direction = direction

    def to_str(self):
        return self.direction

    @staticmethod
    def allActions():
        action_set = []
        for direction in [ActionMaze.NONE, ActionMaze.NORTH, ActionMaze.SOUTH, ActionMaze.EAST, ActionMaze.WEST]:
            action_set.append(ActionMaze(direction))
        return action_set
