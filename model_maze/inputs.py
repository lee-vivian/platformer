"""
Input Handler Object
"""

import pygame
from model_maze.action import ActionMaze

class InputsMaze:
    def __init__(self):
        self.direction = ActionMaze.NONE

    def onLoop(self):
        self.direction = ActionMaze.NONE
        
    def onEvent(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_LEFT, ord('a')]:
                self.direction = ActionMaze.WEST
            elif event.key in [pygame.K_RIGHT, ord('d')]:
                self.direction = ActionMaze.EAST
            elif event.key in [pygame.K_UP, ord('w')]:
                self.direction = ActionMaze.NORTH
            elif event.key in [pygame.K_DOWN, ord('s')]:
                self.direction = ActionMaze.SOUTH

    def getAction(self):
        return ActionMaze(self.direction)
