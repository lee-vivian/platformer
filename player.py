import pygame
import os

import state
import action

'''
Player Object
'''

ALPHA = (0, 0, 0)
GRAVITY = 4
MAX_VEL = 8 * GRAVITY
STEPS = 5
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
        self.onground = False
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

    def reset(self, tile_dim):
        self.rect.x = tile_dim
        self.rect.y = tile_dim
        self.control_dx = 0
        self.onground = False

    def control(self, x):
        # left and right arrows cancel each other out
        if self.control_dx == -x:
            self.control_dx = 0
        else:
            self.control_dx = x

    def gravity(self):
        self.movey += GRAVITY
        if self.movey > MAX_VEL:
            self.movey = MAX_VEL

    def jump(self):
        if self.onground:
            self.movey = -MAX_VEL
            self.onground = False

    @staticmethod
    def get_height_jumped(player_x, player_y, movex, platform_list):
        player_xlo = player_x
        player_xhi = player_x + PLAYER_W

        # increase xrange if jumping AND moving left or right
        if movex < 0:
            player_xlo -= STEPS
        elif movex > 0:
            player_xhi += STEPS

        jump_heights = [MAX_VEL]
        for tile in platform_list:
            # if tile is positioned within y jumping range
            if player_y - MAX_VEL < tile.rect.y + TILE <= player_y:
                # if tile positioned is within x moving range
                if tile.rect.x < player_xhi and tile.rect.x + TILE > player_xlo:
                    jump_heights.append(player_y - (tile.rect.y + TILE))

        return min(jump_heights)

    @staticmethod
    def get_distance_moved(player_x, player_y, movex, platform_list):
        '''if jumping, pass returned state from jumping into update function first'''

        if movex == 0:
            return 0

        move_distances = [STEPS]
        # check adjacent tiles in path that result in collision
        adjacent_tiles = [t for t in platform_list if t.rect.y == player_y]
        if movex < 0:
            for t in adjacent_tiles:
                if player_x - STEPS < t.rect.x + TILE <= player_x:
                    move_distances.append(player_x - (t.rect.x + TILE))
        else:
            for t in adjacent_tiles:
                if player_x + PLAYER_W <= t.rect.x < player_x + PLAYER_W + STEPS:
                    move_distances.append(t.rect.x - (player_x + PLAYER_W))

        return min(move_distances)


    # @staticmethod
    # def next_state(state, action, platform_list):
    #
    #     # currently on ground
    #     if state.onground:
    #         if state.jump:
    #
    #         else:
    #
    #     # not on ground
    #     else:





    def goal_achieved(self, goal_list):
        goal_hit_list = pygame.sprite.spritecollide(self, goal_list, False)
        return len(goal_hit_list) > 0

    def update(self, platform_list, goal_list):
        if self.goal_achieved(goal_list):
            print("Cowabunga!")
            return

        self.movex = self.control_dx
        self.onground = False

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
                    self.onground = True

                self.movey = 0
                break

