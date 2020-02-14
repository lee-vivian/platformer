import pygame
import os

'''
Tile Object
'''


class Tile(pygame.sprite.Sprite):
    def __init__(self, xloc, yloc, img_file, alpha=None):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load(os.path.join('images', img_file)).convert()
        if alpha is not None:
            img.convert_alpha()
            img.set_colorkey(alpha)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.x = xloc
        self.rect.y = yloc

