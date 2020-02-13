import pygame
import os

'''
Tile Object
'''


class Tile(pygame.sprite.Sprite):
    def __init__(self, xloc, yloc, imgw, imgh, img_file):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(os.path.join('images', img_file)).convert()
        self.rect = self.image.get_rect()
        self.rect.x = xloc
        self.rect.y = yloc

