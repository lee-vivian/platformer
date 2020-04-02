from model_maze.state import StateMaze
from model_maze.action import ActionMaze
from model.level import TILE_DIM

'''
Player Model Object
'''

# Player Model constants
HALF_TURTLE_WIDTH = int(74 / 2)
HALF_TILE_WIDTH = int(TILE_DIM / 2)


class PlayerMaze:

    def __init__(self, img, start_tile_coord, game=None):
        self.state = None
        self.half_player_h = HALF_TILE_WIDTH
        self.half_player_w = HALF_TURTLE_WIDTH if img == 'turtle' else HALF_TILE_WIDTH
        self.start_tile_coord = start_tile_coord
        self.reset()

    def start_state(self):
        start_x = self.start_tile_coord[0]
        start_y = self.start_tile_coord[1]
        return StateMaze(x=start_x + self.half_player_w, y=start_y + self.half_player_h, is_start=True, goal_reached=False)

    def reset(self):
        self.state = self.start_state()

    def collide(self, x, y, tile_coords):
        for tile_coord in tile_coords:
            x_overlap = tile_coord[0] < (x + self.half_player_w) and (tile_coord[0] + TILE_DIM) > (x - self.half_player_w)
            y_overlap = tile_coord[1] < (y + self.half_player_h) and (tile_coord[1] + TILE_DIM) > (y - self.half_player_h)
            if x_overlap and y_overlap:
                return True
        return False

    def next_state(self, state, action, platform_coords, goal_coords):
        new_state = state.clone()

        if new_state.goal_reached:
            return new_state

        dx = 0
        dy = 0
        if action.direction == ActionMaze.NORTH:
            dy = -TILE_DIM
        elif action.direction == ActionMaze.SOUTH:
            dy = TILE_DIM
        elif action.direction == ActionMaze.EAST:
            dx = TILE_DIM
        elif action.direction == ActionMaze.WEST:
            dx = -TILE_DIM

        if not self.collide(new_state.x + dx, new_state.y + dy, platform_coords):
            new_state.x += dx
            new_state.y += dy

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
                    self.state = StateMaze.from_str(edge_dest)
                    break
