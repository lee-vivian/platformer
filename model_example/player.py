from model_example.state import StateExample
from model_example.action import ActionExample
from model.level import TILE_DIM

'''
Player Model Object
'''

# Player Model constants
HALF_TURTLE_WIDTH = int(74 / 2)
HALF_TILE_WIDTH = int(TILE_DIM / 2)


class PlayerExample:

    def __init__(self, img, level):
        if img != 'block_half':
            raise RuntimeError('use --player_img block_half for example')

        self.half_player_h = 10
        self.half_player_w = 10

        self.level = level
        self.state = None
        self.reset()

    def get_start_state(self):
        start_x, start_y = self.level.get_start_coord()
        start_x += self.half_player_w
        start_y += self.half_player_h * 3
        return StateExample(x=start_x, y=start_y, is_start=True, goal_reached=False)

    def reset(self):
        self.state = self.get_start_state()

    def is_dead(self):
        return False

    def goal_reached(self):
        return self.state.goal_reached

    def get_hit_bonus_coord(self):
        return None

    def collide(self, x, y, tile_coords):
        for tile_coord in tile_coords:
            x_overlap = tile_coord[0] < (x + self.half_player_w) and (tile_coord[0] + TILE_DIM) > (x - self.half_player_w)
            y_overlap = tile_coord[1] < (y + self.half_player_h) and (tile_coord[1] + TILE_DIM) > (y - self.half_player_h)
            if x_overlap and y_overlap:
                return tile_coord
        return None

    def next_state(self, state, action):
        new_state = state.clone()
        if new_state.goal_reached:
            return new_state

        # Get level bounds
        min_x, max_x = 0 + self.half_player_w, self.level.get_width() - self.half_player_w
        min_y, max_y = 0 + self.half_player_h, self.level.get_height() - self.half_player_h

        if action.direction == ActionExample.RIGHT or action.direction == ActionExample.LEFT:
            dx = 0
            if action.direction == ActionExample.RIGHT:
                dx = TILE_DIM / 2
            elif action.direction == ActionExample.LEFT:
                dx = -TILE_DIM / 2

            move_off_screen = not (min_x <= new_state.x + dx <= max_x)
            block_tile_collision_coord = self.collide(new_state.x + dx, new_state.y, self.level.get_platform_coords())

            if block_tile_collision_coord is None and not move_off_screen:
                new_state.x += dx

        if action.direction == ActionExample.RIGHT or action.direction == ActionExample.LEFT or action.direction == ActionExample.DOWN:
            dy = TILE_DIM / 2

            move_off_screen = not (min_y <= new_state.y + dy <= max_y)
            block_tile_collision_coord = self.collide(new_state.x, new_state.y + dy, self.level.get_platform_coords())

            if block_tile_collision_coord is None and not move_off_screen:
                new_state.y += dy

        if action.direction == ActionExample.UP:
            if state.y + TILE_DIM / 4 >= max_y or self.collide(state.x, state.y + TILE_DIM / 4, self.level.get_platform_coords()):
                dy = -TILE_DIM

                move_off_screen = not (min_y <= new_state.y + dy <= max_y)
                block_tile_collision_coord = self.collide(new_state.x, new_state.y + dy, self.level.get_platform_coords())

                if block_tile_collision_coord is None and not move_off_screen:
                    new_state.y += dy

        new_state.is_start = False
        new_state.goal_reached = False if self.collide(new_state.x, new_state.y, self.level.get_goal_coords()) == None else True

        return new_state

    def update(self, action, precomputed_graph=None, edge_actions_dict=None):

        if precomputed_graph is None or edge_actions_dict is None:
            self.state = self.next_state(self.state, action)
        else:
            action_str = action.to_str()
            state_edges = precomputed_graph.edges(self.state.to_str())
            for edge in state_edges:
                if action_str in edge_actions_dict[edge]:
                    edge_dest = edge[1]
                    self.state = StateExample.from_str(edge_dest)
                    break
