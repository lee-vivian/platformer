import pygame
import os

'''
Player Object
'''

ALPHA = (0, 0, 0)
GRAVITY = 5
PLAYER_W = 74
PLAYER_H = 40

class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.movex = 0  # move along X
        self.movey = 0  # move along Y
        self.frame = 0  # count frames
        img_right = pygame.image.load(os.path.join('images', 'player_right.png')).convert()
        img_left = pygame.image.load(os.path.join('images', 'player_left.png')).convert()
        img_right.convert_alpha()
        img_right.set_colorkey(ALPHA)
        img_left.convert_alpha()
        img_left.set_colorkey(ALPHA)
        self.images = [img_left, img_right]
        self.image = self.images[1]
        self.rect = self.image.get_rect()

    def control(self, x, y):
        self.movex += x
        self.movey += y

    def on_tile(self, all_tiles):
        player_on_tile = [self.rect.y + PLAYER_H == y and self.rect.x <= x <= self.rect.x + PLAYER_W
                          for (x, y) in all_tiles]
        return any(player_on_tile)

    def is_valid_x_move(self, world_x, tile_dim):
        return 0 <= self.rect.x + self.movex < world_x - tile_dim

    def is_valid_y_move(self, world_y):
        return 0 <= self.rect.y + self.movey < world_y - PLAYER_H

    def update(self, world_x, world_y, tile_dim, all_tiles):
        if not self.on_tile(all_tiles):
            self.rect.y += GRAVITY
        if self.is_valid_x_move(world_x, tile_dim):
            self.rect.x += self.movex
        if self.is_valid_y_move(world_y):
            self.rect.y += self.movey
        if self.movex < 0:
            self.frame += 1
            self.image = self.images[0]
        elif self.movex > 0:
            self.frame += 1
            self.image = self.images[1]
