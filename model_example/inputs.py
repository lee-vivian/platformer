"""
Input Handler Object
"""

import pygame
from model_example.action import ActionExample

class InputsExample:
    def __init__(self):
        self.direction = ActionExample.NONE

    def onLoop(self):
        self.direction = ActionExample.NONE
        
    def onEvent(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_LEFT, ord('a')]:
                self.direction = ActionExample.LEFT
            elif event.key in [pygame.K_RIGHT, ord('d')]:
                self.direction = ActionExample.RIGHT
            elif event.key in [pygame.K_UP, ord('w')]:
                self.direction = ActionExample.UP
            elif event.key in [pygame.K_DOWN, ord('s')]:
                self.direction = ActionExample.DOWN

    def getAction(self):
        return ActionExample(self.direction)
