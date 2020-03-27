"""
Player Action Object
"""


class ActionPlatformer:
    def __init__(self, left, right, jump):
        self.left = left
        self.right = right
        self.jump = jump

    def to_str(self):
        action_string = ""
        if self.jump:
            action_string += "J"
        if self.left:
            action_string += "L"
        if self.right:
            action_string += "R"
        if action_string == "":
            action_string = "X"
        return action_string

    @staticmethod
    def allActions():
        action_set = []
        for left in [True, False]:
            for right in [True, False]:
                for jump in [True, False]:
                    action_set.append(ActionPlatformer(left, right, jump))
        return action_set
