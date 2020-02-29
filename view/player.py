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
        img_right = pygame.image.load(os.path.join('images', img + '_right.png')).convert()
        img_left = pygame.image.load(os.path.join('images', img + '_left.png')).convert()
        img_right.convert_alpha()
        img_right.set_colorkey(ALPHA)
        img_left.convert_alpha()
        img_left.set_colorkey(ALPHA)
        self.images = [img_left, img_right]
        self.image = self.images[1]
        self.rect = self.image.get_rect()

    def update(self, player_model):
        self.image = self.images[1] if player_model.state.facing_right else self.images[0]
        self.rect = self.image.get_rect()
        self.rect.x = player_model.state.x - player_model.half_player_w
        self.rect.y = player_model.state.y - player_model.half_player_h
