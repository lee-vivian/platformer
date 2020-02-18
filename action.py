"""
Player Action Object
"""


class Action:
    def __init__(self, jump, right, left):
        self.jump = jump
        self.right = right
        self.left = left

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







