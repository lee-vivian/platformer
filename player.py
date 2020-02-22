import pygame
import os

from state import State

'''
Player Object
'''

# Player constants
ALPHA = (0, 0, 0)
GRAVITY = 4
MAX_VEL = 7 * GRAVITY
STEPS = 5
PLAYER_W = 74
PLAYER_H = 40
JUMP = 30

# Level constants
TILE = 40


class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.state = None
        self.reset()
        img_right = pygame.image.load(os.path.join('images', 'player_right.png')).convert()
        img_left = pygame.image.load(os.path.join('images', 'player_left.png')).convert()
        img_right.convert_alpha()
        img_right.set_colorkey(ALPHA)
        img_left.convert_alpha()
        img_left.set_colorkey(ALPHA)
        self.images = [img_left, img_right]
        self.image = self.images[1]
        self.rect = self.image.get_rect()

    @staticmethod
    def start_state():
        return State(TILE, TILE, 0, GRAVITY, True, False, False)

    def reset(self):
        self.state = Player.start_state()

    @staticmethod
    def collide(x, y, tile_list):
        for tile in tile_list:
            x_overlap = tile.rect.x < (x + PLAYER_W) and (tile.rect.x + TILE) > x
            y_overlap = tile.rect.y < (y + PLAYER_H) and (tile.rect.y + TILE) > y
            if x_overlap and y_overlap:
                return True
        return False

    @staticmethod
    def str_to_state(string):
        state_dict = eval(string)
        return State(state_dict['x'], state_dict['y'],
                     state_dict['movex'], state_dict['movey'],
                     state_dict['facing_right'], state_dict['onground'], state_dict['goal_reached'])

    @staticmethod
    def next_state(state, action, platform_list, goal_list):
        new_state = state.clone()

        if new_state.goal_reached:
            return new_state

        new_state.movey += GRAVITY
        if new_state.movey > MAX_VEL:
            new_state.movey = MAX_VEL

        if action.left and not action.right:
            new_state.movex = -STEPS
        elif action.right and not action.left:
            new_state.movex = STEPS
        else:
            new_state.movex = 0

        if action.jump and new_state.onground:
            new_state.movey = -MAX_VEL

        if new_state.movex < 0:
            new_state.facing_right = False
        if new_state.movex > 0:
            new_state.facing_right = True

        for ii in range(abs(new_state.movex)):
            old_x = new_state.x
            if new_state.movex < 0:
                new_state.x -= 1
            elif new_state.movex > 0:
                new_state.x += 1

            if Player.collide(new_state.x, new_state.y, platform_list):
                new_state.x = old_x
                new_state.movex = 0
                break

        new_state.onground = False

        for jj in range(abs(new_state.movey)):
            old_y = new_state.y
            if new_state.movey < 0:
                new_state.y -= 1
            elif new_state.movey > 0:
                new_state.y += 1

            if Player.collide(new_state.x, new_state.y, platform_list):
                new_state.y = old_y
                if new_state.movey > 0:
                    new_state.onground = True
                new_state.movey = 0
                break

        if Player.collide(new_state.x, new_state.y, goal_list):
            new_state.goal_reached = True

        return new_state

    def update(self, action, platform_list, goal_list, precomputed_graph, edge_actions_dict):

        if precomputed_graph is None or edge_actions_dict is None:
            self.state = Player.next_state(self.state, action, platform_list, goal_list)
        else:
            action_str = action.to_str()
            state_edges = precomputed_graph.edges(self.state.to_str())
            for edge in state_edges:
                if action_str in edge_actions_dict[edge]:
                    edge_dest = edge[1]
                    self.state = Player.str_to_state(edge_dest)
                    break

        self.image = self.images[1] if self.state.facing_right else self.images[0]
        self.rect = self.image.get_rect()
        self.rect.x = self.state.x
        self.rect.y = self.state.y
