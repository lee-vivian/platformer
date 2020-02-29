import pygame
import os

'''
Tile Object
'''

PIZZA_ALPHA = (255, 255, 255)


class Tile(pygame.sprite.Sprite):
    def __init__(self, xloc, yloc, img_file, alpha=None):

        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load(os.path.join('images', img_file)).convert()

        if img_file == 'pizza.png':
            alpha = PIZZA_ALPHA

        if alpha is not None:
            img.convert_alpha()
            img.set_colorkey(alpha)

        self.image = img
        self.rect = self.image.get_rect()
        self.rect.x = xloc
        self.rect.y = yloc

