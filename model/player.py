from model.state import State
from model.level import TILE_DIM

'''
Player Model Object
'''

# Player Model constants
GRAVITY = 4
MAX_VEL = 10 * GRAVITY
STEPS = 8


class Player:

    def __init__(self, img, start_tile_coord):
        self.state = None
        self.half_player_h = int(40 / 2)
        if img == 'turtle':
            self.half_player_w = int(74 / 2)
        else:
            self.half_player_w = int(40 / 2)
        self.start_tile_coord = start_tile_coord
        self.reset()

    @staticmethod
    def str_to_state(string):
        state_dict = eval(string)
        return State(state_dict['x'], state_dict['y'],
                     state_dict['movex'], state_dict['movey'],
                     state_dict['facing_right'], state_dict['onground'], state_dict['goal_reached'])

    def start_state(self):
        start_x = self.start_tile_coord[0]
        start_y = self.start_tile_coord[1]
        return State(start_x + self.half_player_w, start_y + self.half_player_h,
                     0, GRAVITY, True, True, False)

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

            if self.collide(new_state.x, new_state.y, platform_coords):
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

        if self.collide(new_state.x, new_state.y, goal_coords):
            new_state.goal_reached = True

        return new_state

    def update(self, action, platform_coords, goal_coords, precomputed_graph, edge_actions_dict):
        if precomputed_graph is None or edge_actions_dict is None:
            self.state = self.next_state(self.state, action, platform_coords, goal_coords)
        else:
            action_str = action.to_str()
            state_edges = precomputed_graph.edges(self.state.to_str())
            for edge in state_edges:
                if action_str in edge_actions_dict[edge]:
                    edge_dest = edge[1]
                    self.state = Player.str_to_state(edge_dest)
                    break
