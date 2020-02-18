"""
Player Action Object
"""


class Action:
    def __init__(self, left, right, jump):
        self.left = left
        self.right = right
        self.jump = jump

    @staticmethod
    def str_to_action(x):
        jump = 'J' in x
        right = 'R' in x
        left = 'L' in x
        return Action(jump, right, left)

    @staticmethod
    def strings_to_actions(strings):
        action_list = []
        for s in strings:
            action_list.append(Action.str_to_action(s))







