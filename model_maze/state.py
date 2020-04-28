"""
Player State Object
"""


class StateMaze:
    def __init__(self, x, y, is_start, goal_reached, score, uncollected_bonus_coords, collected_bonus_coords):
        self.x = x  # x coord of center of player
        self.y = y  # y coord of center of player
        self.is_start = is_start
        self.goal_reached = goal_reached
        self.score = score
        self.uncollected_bonus_coords = uncollected_bonus_coords
        self.collected_bonus_coords = collected_bonus_coords

    def clone(self):
        return StateMaze(self.x, self.y, self.is_start, self.goal_reached,
                         self.score, self.uncollected_bonus_coords, self.collected_bonus_coords)

    def to_abrv_str(self):
        string = "{"
        string += "'x': " + str(self.x) + ", "
        string += "'y': " + str(self.y) + ", "
        string += "'is_start': " + str(self.is_start) + ", "
        string += "'goal_reached': " + str(self.goal_reached)
        string += "}"
        return string

    def to_str(self):
        self.uncollected_bonus_coords.sort()
        self.collected_bonus_coords.sort()
        string = "{"
        string += "'x': " + str(self.x) + ", "
        string += "'y': " + str(self.y) + ", "
        string += "'is_start': " + str(self.is_start) + ", "
        string += "'goal_reached': " + str(self.goal_reached) + ", "
        string += "'score': " + str(self.score) + ", "
        string += "'uncollected_bonus_coords': " + str(self.uncollected_bonus_coords) + ", "
        string += "'collected_bonus_coords': " + str(self.collected_bonus_coords)
        string += "}"
        return string

    @staticmethod
    def from_abrv_str(string):
        state_dict = eval(string)
        return StateMaze(state_dict['x'], state_dict['y'], state_dict['is_start'], state_dict['goal_reached'],
                         score=None, uncollected_bonus_coords=None, collected_bonus_coords=None)

    @staticmethod
    def from_str(string):
        state_dict = eval(string)
        return StateMaze(state_dict['x'], state_dict['y'], state_dict['is_start'], state_dict['goal_reached'],
                         state_dict['score'], state_dict['uncollected_bonus_coords'], state_dict['collected_bonus_coords'])
