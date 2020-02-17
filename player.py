import pygame
import os

from state import State
from action import Action

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

    @staticmethod
    def get_height_jumped(x, y, movex, platform_list):
        player_xlo = x
        player_xhi = x + PLAYER_W

        # increase xrange if jumping AND moving left or right
        if movex < 0:
            player_xlo -= STEPS
        elif movex > 0:
            player_xhi += STEPS

        jump_heights = [MAX_VEL]
        for tile in platform_list:
            # if tile is positioned within y jumping range
            if y - MAX_VEL < tile.rect.y + TILE <= y:
                # if tile positioned is within x moving range
                if tile.rect.x < player_xhi and tile.rect.x + TILE > player_xlo:
                    jump_heights.append(y - (tile.rect.y + TILE))

        return min(jump_heights)

    @staticmethod
    def get_height_fallen(x, y, movex, platform_list):
        player_xlo = x
        player_xhi = x + PLAYER_W

        # increase xrange if falling AND moving left or right
        if movex < 0:
            player_xlo -= STEPS
        elif movex > 0:
            player_xhi += STEPS

        fall_heights = [GRAVITY]
        for tile in platform_list:
            # if tile is positioned within y falling range
            if y + PLAYER_H <= tile.rect.y < y + PLAYER_H + GRAVITY:
                # if tile is positioned within x falling range
                if tile.rect.x < player_xhi and tile.rect.x + TILE > player_xlo:
                    fall_heights.append(tile.rect.y - (y + PLAYER_H))

        return min(fall_heights)

    @staticmethod
    def get_distance_moved(x, y, movex, platform_list):
        # UPDATE MOVEMENT IN Y DIRECTION FIRST
        if movex == 0:
            return 0

        move_distances = [STEPS]
        # check adjacent tiles in path that result in collision
        adjacent_tiles = [t for t in platform_list if t.rect.y == y]
        if movex < 0:
            for t in adjacent_tiles:
                if x - STEPS < t.rect.x + TILE <= x:
                    move_distances.append(x - (t.rect.x + TILE))
        else:
            for t in adjacent_tiles:
                if x + PLAYER_W <= t.rect.x < x + PLAYER_W + STEPS:
                    move_distances.append(t.rect.x - (x + PLAYER_W))

        dist_moved = min(move_distances)
        return dist_moved if movex > 0 else dist_moved * -1

    @staticmethod
    def player_on_ground(x, y, platform_list):
        player_xlo = x
        player_xhi = x + PLAYER_W
        for tile in platform_list:
            if tile.rect.y == y + PLAYER_H and tile.rect.x < player_xhi and tile.rect.x + TILE > player_xlo:
                return True
        return False

    @staticmethod
    def next_state(state, action, platform_list):

        new_x = 0 + state.x
        new_y = 0 + state.y
        if action.left != action.right:
            new_move_x = STEPS if action.right else -STEPS
        else:
            new_move_x = 0

        # on ground - may or may not be jumping
        if state.onground:
            # state does not change
            if (action.left and action.right) or (not action.jump and not action.left and not action.right):
                return State(state.x, state.y, state.movex, state.onground)

            # jump up
            if action.jump:
                new_y -= Player.get_height_jumped(new_x, new_y, new_move_x, platform_list)

        # not on ground - always falling due to gravity
        else:
            # fall down
            height_fallen = Player.get_height_fallen(new_x, new_y, new_move_x, platform_list)
            new_y += height_fallen

        # move horizontally
        new_x += Player.get_distance_moved(new_x, new_y, new_move_x, platform_list)

        # check if on ground
        new_on_ground = Player.player_on_ground(new_x, new_y, platform_list)

        return State(new_x, new_y, new_move_x, new_on_ground)
