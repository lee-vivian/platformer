from model.level import TILE_DIM
from model_platformer.state import StatePlatformer

from math import inf


'''
Player Model Object
'''

HALF_TURTLE_WIDTH = int(74 / 2)
HALF_TILE_WIDTH = int(TILE_DIM / 2)


class PlayerPlatformer:

    def __init__(self, img, start_tile_coord, game=None):
        if game == 'sample':
            self.gravity = 4
            self.steps = 8
        else:
            self.gravity = 5
            self.steps = 10
        self.max_vel = 8 * self.gravity

        self.state = None
        self.half_player_h = HALF_TILE_WIDTH
        self.half_player_w = HALF_TURTLE_WIDTH if img == 'turtle' else HALF_TILE_WIDTH
        self.start_tile_coord = start_tile_coord
        self.reset()

    def start_state(self):
        start_x = self.start_tile_coord[0]
        start_y = self.start_tile_coord[1]
        return StatePlatformer(x=start_x + self.half_player_w, y=start_y + self.half_player_h, movex=0, movey=self.gravity,
                     onground=True, is_start=True, goal_reached=False)

    def reset(self):
        self.state = self.start_state()

    def collide(self, x, y, tile_coords):
        for tile_coord in tile_coords:
            x_overlap = tile_coord[0] < (x + self.half_player_w) and (tile_coord[0] + TILE_DIM) > (x - self.half_player_w)
            y_overlap = tile_coord[1] < (y + self.half_player_h) and (tile_coord[1] + TILE_DIM) > (y - self.half_player_h)
            if x_overlap and y_overlap:
                return True
        return False

    def get_xy_bounds(self, platform_coords):
        tile_min_x, tile_max_x = inf, -inf  # leftmost and rightmost
        tile_min_y, tile_max_y = 0, -inf  # ceiling and floor

        for x, y in platform_coords:
            tile_min_x = min(tile_min_x, x)
            tile_max_x = max(tile_max_x, x)
            tile_max_y = max(tile_max_y, y)

        return (tile_min_x + self.half_player_w, tile_max_x + self.half_player_w,
                tile_min_y + self.half_player_h, tile_max_y + self.half_player_h)

    def next_state(self, state, action, platform_coords, goal_coords):

        new_state = state.clone()

        if new_state.goal_reached:
            return new_state

        min_x, max_x, min_y, max_y = self.get_xy_bounds(platform_coords)  # bounds to prevent player moving off screen

        new_state.movey += self.gravity
        if new_state.movey > self.max_vel:
            new_state.movey = self.max_vel

        if action.left and not action.right:
            new_state.movex = -self.steps
        elif action.right and not action.left:
            new_state.movex = self.steps
        else:
            new_state.movex = 0

        if action.jump and new_state.onground:
            new_state.movey = -self.max_vel

        for ii in range(abs(new_state.movex)):
            old_x = new_state.x
            if new_state.movex < 0:
                new_state.x -= 1
            elif new_state.movex > 0:
                new_state.x += 1

            if self.collide(new_state.x, new_state.y, platform_coords) or new_state.x < min_x or new_state.x > max_x:
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

            if self.collide(new_state.x, new_state.y, platform_coords):
                new_state.y = old_y
                if new_state.movey > 0:
                    new_state.onground = True
                new_state.movey = 0
                break

        if new_state.y > max_y + TILE_DIM * 10:  # reset position if player falls off the screen (e.g. in a pit)
            return self.start_state()

        new_state.is_start = False
        new_state.goal_reached = self.collide(new_state.x, new_state.y, goal_coords)

        return new_state

    def update(self, action, platform_coords, goal_coords, precomputed_graph=None, edge_actions_dict=None):
        if precomputed_graph is None or edge_actions_dict is None:
            self.state = self.next_state(self.state, action, platform_coords, goal_coords)
        else:
            action_str = action.to_str()
            state_edges = precomputed_graph.edges(self.state.to_str())
            for edge in state_edges:
                if action_str in edge_actions_dict[edge]:
                    edge_dest = edge[1]
                    self.state = StatePlatformer.from_str(edge_dest)
                    break

