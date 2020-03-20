import pygame
import os

'''
Player View Object
'''

# Player View constants
ALPHA = (0, 0, 0)


class Player(pygame.sprite.Sprite):
    def __init__(self, img):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load(os.path.join('images', img + '.png')).convert()
        self.image = img
        self.rect = self.image.get_rect()

    def update(self, x, y, half_w, half_h):
        self.rect = self.image.get_rect()
        self.rect.x = x - half_w
        self.rect.y = y - half_h
