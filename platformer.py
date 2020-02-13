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
player.rect.x = 0
player.rect.y = 360
player_list = pygame.sprite.Group()
player_list.add(player)
STEPS = 5  # num pixels to move per step
JUMP = 8

# Level
LEVEL = 1
level = level.Level()
ground_list = level.ground(LEVEL, WORLDX, WORLDY, TILE)
platform_list = level.platform(LEVEL, TILE)
all_tile_coords = []
all_tile_coords += level.get_ground_coords(LEVEL, WORLDX, WORLDY, TILE)
all_tile_coords += level.get_platform_coords(LEVEL)

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
                print("jump")
                # player.control(0, -JUMP)

        if event.type == pygame.KEYUP:
            if event.key in [pygame.K_LEFT, ord('a')]:
                player.control(STEPS, 0)  # returns sprite momentum to 0
            elif event.key in [pygame.K_RIGHT, ord('d')]:
                player.control(-STEPS, 0)  # returns sprite momentum to 0
            elif event.key in [pygame.K_SPACE, pygame.K_UP, ord('w')]:
                print("jump")
                # player.control(0, JUMP)

    world.blit(backdrop, backdropbox)
    player.update(WORLDX, WORLDY, TILE, all_tile_coords)
    player_list.draw(world)  # draw player
    ground_list.draw(world)  # draw ground tiles
    platform_list.draw(world)  # draw platforms tiles
    pygame.display.flip()
    clock.tick(FPS)
