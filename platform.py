import pygame
import os

'''
Platform Object
'''

class Platform(pygame.sprite.Sprite):
    def __init__(self, xloc, yloc, imgw, imgh, img):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(os.path.join('images', img)).convert()
        self.rect = self.image.get_rect()
        self.rect.x = xloc
        self.rect.y = yloc

        