'''
Camera Object to Scroll if Level is larger than window
'''

import pygame


class Camera:
    def __init__(self, camera_function, width, height, world_x, world_y):
        self.camera_function = camera_function
        self.state = pygame.Rect(0, 0, width, height)
        self.world_dim = (world_x, world_y)

    def apply(self, target):
        return target.rect.move(self.state.topleft)  # recalculate position of target on screen to scroll

    def update(self, target):
        self.state = self.camera_function(self.state, target.rect, self.world_dim)

    @staticmethod
    def camera_function(camera_state, target_rect, world_dim):

        # center target_rect
        x = -target_rect.center[0] + world_dim[0] / 2
        y = -target_rect.center[1] + world_dim[1] / 2
        # move camera
        camera_state.topleft += (pygame.Vector2((x, y)) - pygame.Vector2(camera_state.topleft)) * 0.06
        # prevent camera from moving outside the viewport
        camera_state.x = max(-(camera_state.width - world_dim[0]), min(0, camera_state.x))
        camera_state.y = max(-(camera_state.height - world_dim[1]), min(0, camera_state.y))

        return camera_state

