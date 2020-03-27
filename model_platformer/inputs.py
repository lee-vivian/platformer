"""
Input Handler Object
"""

import pygame
from model_platformer.action import ActionPlatformer

class InputsPlatformer:
    def __init__(self):
        self.key_left = False
        self.key_right = False
        self.key_jump = False

    def onLoop(self):
        self.key_jump = False
        
    def onEvent(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_LEFT, ord('a')]:
                self.key_left = True
            elif event.key in [pygame.K_RIGHT, ord('d')]:
                self.key_right = True
            elif event.key in [pygame.K_SPACE, pygame.K_UP, ord('w')]:
                self.key_jump = True

        if event.type == pygame.KEYUP:
            if event.key in [pygame.K_LEFT, ord('a')]:
                self.key_left = False
            elif event.key in [pygame.K_RIGHT, ord('d')]:
                self.key_right = False

    def getAction(self):
        return ActionPlatformer(self.key_left, self.key_right, self.key_jump)
