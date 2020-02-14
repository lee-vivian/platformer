'''
Basic Platform Game
author: Vivian Lee
created: 02-12-2020
acknowledgements: followed tutorial from opensource.com
'''

import pygame
import sys
import os
import player
import level

'''
Setup
'''

# Background
WORLDX = 960
WORLDY = 720
TILE = 40
FPS = 40  # frame rate
ANI = 4  # animation cycles
clock = pygame.time.Clock()
pygame.init()
world = pygame.display.set_mode([WORLDX, WORLDY])
backdrop = pygame.image.load(os.path.join('images', 'platform_bkgd.png')).convert()
backdropbox = world.get_rect()

# Player
player = player.Player()
player.reset(TILE)
player_list = pygame.sprite.Group()
player_list.add(player)
STEPS = 5  # num pixels to move per step

# Level
LEVEL = 1
level = level.Level()
platform_list = level.platform(LEVEL, TILE, WORLDX, WORLDY)
goal_list = level.goal(LEVEL)

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
            elif event.key == ord('r'):
                player.reset(TILE)
            elif event.key in [pygame.K_LEFT, ord('a')]:
                player.control(-STEPS)
            elif event.key in [pygame.K_RIGHT, ord('d')]:
                player.control(STEPS)
            elif event.key in [pygame.K_SPACE, pygame.K_UP, ord('w')]:
                player.jump()

        if event.type == pygame.KEYUP:
            if event.key in [pygame.K_LEFT, ord('a')]:
                player.control(0)  # stop moving, set velocity to 0
            elif event.key in [pygame.K_RIGHT, ord('d')]:
                player.control(0)  # stop moving, set velocity to 0

    world.blit(backdrop, backdropbox)
    player.gravity()
    player.update(platform_list)
    player_list.draw(world)  # draw player
    platform_list.draw(world)  # draw platforms tiles
    goal_list.draw(world)  # draw goal tiles
    pygame.display.flip()
    clock.tick(FPS)
