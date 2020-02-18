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
    def next_state(state, action, platform_list):

        left_and_right = action.left and action.right

        # can only jump when on ground and not pressing left and right simultaneously
        jumping = action.jump and state.movey == 0 and not left_and_right
        falling = state.movey > 0

        # player x movement range
        player_xlo = state.x
        player_xhi = state.x + PLAYER_W

        if not left_and_right:
            if action.left:
                player_xlo -= STEPS
                player_xhi -= STEPS
            elif action.right:
                player_xlo += STEPS
                player_xhi += STEPS

        # state attributes to update
        new_x = 0 + state.x
        new_y = 0 + state.y
        new_movex = 0 + state.movex
        new_movey = 0 + state.movey
        new_facing_right = state.facing_right

        # handle jumping and falling
        if jumping or falling:

            # player y movement range
            max_y_delta = MAX_VEL if jumping else GRAVITY
            y_deltas = [max_y_delta]
            y_lo = state.y - MAX_VEL if jumping else state.y + PLAYER_H
            y_hi = state.y if jumping else state.y + PLAYER_H + GRAVITY

            # check ceilings if jumping and floors if falling
            tile_y_addition = TILE if jumping else 0

            # check for collisions
            for tile in platform_list:
                tile_in_y_path = y_lo <= (tile.rect.y + tile_y_addition) <= y_hi
                tile_in_x_path = tile.rect.x < player_xhi and tile.rect.x + TILE > player_xlo
                if tile_in_y_path and tile_in_x_path:
                    if jumping:
                        y_deltas.append(y_hi - (tile.rect.y + tile_y_addition))
                    else:
                        y_deltas.append(tile.rect.y - y_lo)

            # update state y
            y_delta = min(y_deltas)
            new_y = new_y - y_delta if jumping else new_y + y_delta

            # update state movey
            y_collision_occurred = y_delta < max_y_delta
            if y_collision_occurred:
                new_movey = 0
            elif jumping:
                new_movey = -MAX_VEL

        # handle x movement
        if action.left or action.right:

            # left and right arrows cancel each other out and stop movement
            if left_and_right or (state.movex < 0 and action.right) or (state.movex > 0 and action.left):
                new_movex = 0
            else:
                # get adjacent tiles after jumping or falling
                adjacent_tiles = [t for t in platform_list if t.rect.y == new_y]

                # player x movement range
                max_x_delta = STEPS
                x_deltas = [max_x_delta]
                x_lo = state.x - STEPS if action.left else state.x + PLAYER_W
                x_hi = state.x if action.left else state.x + PLAYER_W + STEPS

                # check right most side of tile if moving left
                tile_x_addition = TILE if action.left else 0

                # check for collisions in x path
                for t in adjacent_tiles:
                    if x_lo <= (t.rect.x + tile_x_addition) <= x_hi:
                        if action.left:
                            x_deltas.append(x_hi - (t.rect.x + tile_x_addition))
                        else:
                            x_deltas.append(t.rect.x - x_lo)

                # update state x
                x_delta = min(x_deltas)
                new_x = new_x - x_delta if action.left else new_x + x_delta

                # update state movex
                x_collision_occured = x_delta < max_x_delta
                if x_collision_occured:
                    new_movex = 0
                elif action.left:
                    new_movex = -STEPS
                else:
                    new_movex = STEPS

                # update state face direction
                new_facing_right = action.right

        # return new state
        return State(new_x, new_y, new_movex, new_movey, new_facing_right)

