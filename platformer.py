'''
Basic Platform Game
author: Vivian Lee
created: 02-12-2020
acknowledgements: followed tutorial from opensource.com
'''

import pygame
import sys
import os

'''
Objects
'''

class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.movex = 0  # move along X
        self.movey = 0  # move along Y
        self.frame = 0  # count frames
        img_right = pygame.image.load(os.path.join('images', 'player_right.png')).convert()
        img_left = pygame.image.load(os.path.join('images', 'player_left.png')).convert()
        self.images = [img_left, img_right]
        self.image = self.images[1]
        self.rect = self.image.get_rect()

    def control(self, x, y):
        self.movex += x
        self.movey += y

    def update(self):
        self.rect.x += self.movex
        self.rect.y += self.movey
        if self.movex < 0:
            self.frame += 1
            self.image = self.images[0]
        elif self.movex > 0:
            self.frame += 1
            self.image = self.images[1]


'''
Setup
'''

# Background
worldx = 960
worldy = 720
fps = 40  # frame rate
ani = 4  # animation cycles
clock = pygame.time.Clock()
pygame.init()
world = pygame.display.set_mode([worldx, worldy])
backdrop = pygame.image.load(os.path.join('images', 'platform_bkgd.png')).convert()
backdropbox = world.get_rect()

# Player
player = Player()
player.rect.x = 0
player.rect.y = 0
player_list = pygame.sprite.Group()
player_list.add(player)
STEPS = 5  # num pixels to move per step

'''
Main Loop
'''

main = True
while main:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            main = False

        if event.type == pygame.KEYDOWN:
            if event.key == ord('q'):
                pygame.quit()
                main = False
                sys.exit()
            elif event.key in [pygame.K_LEFT, ord('a')]:
                player.control(-STEPS, 0)
            elif event.key in [pygame.K_RIGHT, ord('d')]:
                player.control(STEPS, 0)
            elif event.key in [pygame.K_SPACE, pygame.K_UP, ord('w')]:
                print('jump')

        if event.type == pygame.KEYUP:
            if event.key in [pygame.K_LEFT, ord('a')]:
                player.control(STEPS, 0)  # returns sprite momentum to 0
            elif event.key in [pygame.K_RIGHT, ord('d')]:
                player.control(-STEPS, 0)  # returns sprite momentum to 0

    world.blit(backdrop, backdropbox)
    player.update()
    player_list.draw(world)  # draw player
    pygame.display.flip()
    clock.tick(fps)
