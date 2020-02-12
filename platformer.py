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
        img = pygame.image.load(os.path.join('images', 'player.png')).convert()
        self.image = img
        self.rect = self.image.get_rect()


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

'''
Main Loop
'''

main = True
while main is True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            main = False

        if event.type == pygame.KEYDOWN:
            if event.key == ord('q'):
                pygame.quit()
                main = False
                sys.exit()

        world.blit(backdrop, backdropbox)
        player_list.draw(world)  # draw player
        pygame.display.flip()
        clock.tick(fps)
