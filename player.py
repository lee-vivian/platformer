import pygame
import os

'''
Player Object
'''

ALPHA = (0, 0, 0)
GRAVITY = 4
MAX_VEL = 8 * GRAVITY
PLAYER_W = 74
PLAYER_H = 40
WORLDX = 960
WORLDY = 720
TILE = 40
JUMP = 30


class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.movex = 0  # move along X
        self.movey = 0  # move along Y
        self.frame = 0  # count frames
        self.collide_delta = 0
        self.jump_delta = 6
        self.jumping = True
        self.control_dx = 0
        img_right = pygame.image.load(os.path.join('images', 'player_right.png')).convert()
        img_left = pygame.image.load(os.path.join('images', 'player_left.png')).convert()
        img_right.convert_alpha()
        img_right.set_colorkey(ALPHA)
        img_left.convert_alpha()
        img_left.set_colorkey(ALPHA)
        self.images = [img_left, img_right]
        self.image = self.images[1]
        self.rect = self.image.get_rect()

    def reset(self):
        self.rect.x = 0
        self.rect.y = 0
        self.control_dx = 0
        self.control_dy = 0
        self.jumping = False

    def control(self, x):
        self.control_dx = x

    def gravity(self):
        self.movey += GRAVITY
        if self.movey > MAX_VEL:
            self.movey = MAX_VEL
        ##if self.rect.y > WORLDY and self.movey >= 0:
        ##    self.movey = 0
        ##    self.rect.y = WORLDY - TILE * 2

    def jump(self, platform_list):
        if not self.jumping:
            self.movey = -MAX_VEL
            self.jumping = True

    def update(self, ground_list, platform_list):
        self.movex = self.control_dx

        if self.movex < 0:
            self.frame += 1
            self.image = self.images[0]
        elif self.movex > 0:
            self.frame += 1
            self.image = self.images[1]

        for ii in range(abs(self.movex)):
            oldx = self.rect.x
            if self.movex < 0:
                self.rect.x -= 1
            elif self.movex > 0:
                self.rect.x += 1

            platform_hit_list = pygame.sprite.spritecollide(self, platform_list, False)
            if len(platform_hit_list) != 0:
                self.rect.x = oldx
                self.movex = 0
                break

        for ii in range(abs(self.movey)):
            oldy = self.rect.y
            if self.movey < 0:
                self.rect.y -= 1
            elif self.movey > 0:
                self.rect.y += 1

            platform_hit_list = pygame.sprite.spritecollide(self, platform_list, False)
            if len(platform_hit_list) != 0:
                self.rect.y = oldy

                if self.movey > 0:
                    self.jumping = False

                self.movey = 0
                break


        return



        self.rect.x += self.movex
        self.rect.y += self.movey

        # prevent player from moving off screen
        if self.rect.x < 0:
            self.rect.x = 0
        elif self.rect.x + PLAYER_W > WORLDX:
            self.rect.x = WORLDX - PLAYER_W

        # prevent player from running through walls

        platform_hit_list = pygame.sprite.spritecollide(self, platform_list, False)
        for p in platform_hit_list:
            ##self.collide_delta = 0  # stop jumping
            ##self.movey = 0
            # treat platforms like ceilings

            if p.rect.colliderect(self.rect):
                self.rect.y = p.rect.y - PLAYER_H - 1
                ##if p.rect.y <= self.rect.y + PLAYER_H <= p.rect.y + TILE:
                ##    self.rect.y = p.rect.y - PLAYER_H - 1
                ##elif p.rect.y <= self.rect.y <= p.rect.y + TILE:
                ##    self.rect.y = p.rect.y + TILE + 1

            if p.rect.colliderect(self.rect):
                self.rect.x = p.rect.x - PLAYER_W - 1
                ##if self.movex > 0 and p.rect.x <= self.rect.x + PLAYER_W <= p.rect.x + TILE:
                ##    self.rect.x = p.rect.x - PLAYER_W - 1
                ##elif self.movex < 0 and p.rect.x <= self.rect.x <= p.rect.x + TILE:
                ##    self.rect.x = p.rect.x + TILE + 1

            ##if self.rect.y > p.rect.y:
              ##  self.rect.y = p.rect.y + TILE
                # prevent running through wall tiles
                ##if self.movex > 0 and p.rect.x <= self.rect.x + PLAYER_W <= p.rect.x + TILE:
                ##    print("jump delta: ", self.jump_delta)
                ##    self.rect.x = p.rect.x - PLAYER_W
                ##elif self.movex < 0 and p.rect.x <= self.rect.x <= p.rect.x + TILE:
                ##        self.rect.x = p.rect.x + TILE
                # if self.movex != 0:
                #     if self.rect.x < p.rect.x:
                #         self.rect.x = p.rect.x - PLAYER_W
                #     else:
                #         self.rect.x = p.rect.x + TILE
                #
            # treat platforms like floors
            ##else:
              ##  self.rect.y = p.rect.y - TILE



        ground_hit_list = pygame.sprite.spritecollide(self, ground_list, False)
        for g in ground_hit_list:
            self.movey = 0  # turn off gravity if player is on a tile
            self.rect.y = WORLDY - TILE - PLAYER_H
            self.collide_delta = 0  # stop jumping

        if self.collide_delta < 6 and self.jump_delta < 6:
            self.jump_delta = 6*2
            self.movey -= JUMP
            self.collide_delta += 6
            self.jump_delta += 6


