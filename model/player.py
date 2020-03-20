from model.state import State
from model.level import TILE_DIM

'''
Player Model Object
'''

# Player Model constants
GRAVITY = 4
MAX_VEL = 8 * GRAVITY
STEPS = 8

HALF_TURTLE_WIDTH = int(74 / 2)
HALF_TILE_WIDTH = int(TILE_DIM / 2)


class Player:

    def __init__(self, img, start_tile_coord):
        self.state = None
        self.half_player_h = HALF_TILE_WIDTH
        self.half_player_w = HALF_TURTLE_WIDTH if img == 'turtle' else HALF_TILE_WIDTH
        self.start_tile_coord = start_tile_coord
        self.reset()

    @staticmethod
    def metatile_coord_from_state_coord(state_coord, half_player_w, half_player_h):
        return (state_coord[0] - half_player_w) - (state_coord[0] - half_player_w) % TILE_DIM, \
               (state_coord[1] - half_player_h) - (state_coord[1] - half_player_h) % TILE_DIM

    @staticmethod
    def state_in_metatile(metatile_coord, state_coord, half_player_w, half_player_h):
        return metatile_coord == Player.metatile_coord_from_state_coord(state_coord, half_player_w, half_player_h)

    def start_state(self):
        start_x = self.start_tile_coord[0]
        start_y = self.start_tile_coord[1]
        return State(x=start_x + self.half_player_w, y=start_y + self.half_player_h, movex=0, movey=GRAVITY,
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

        new_state.is_start = Player.state_in_metatile(self.start_tile_coord, (new_state.x, new_state.y),
                                                      self.half_player_w, self.half_player_h)

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
                    self.state = State.from_str(edge_dest)
                    break
