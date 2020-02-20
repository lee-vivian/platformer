"""
Player Action Object
"""


class Action:
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








