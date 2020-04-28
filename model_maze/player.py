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

    def __init__(self, img, level):
        self.half_player_h = HALF_TILE_WIDTH
        self.half_player_w = HALF_TURTLE_WIDTH if img == 'turtle' else HALF_TILE_WIDTH

        self.level = level
        self.state = None
        self.reset()

    def get_start_state(self):
        start_x, start_y = self.level.get_start_coord()
        start_x += self.half_player_w
        start_y += self.half_player_h
        return StateMaze(x=start_x, y=start_y, is_start=True, goal_reached=False, score=0,
                         uncollected_bonus_coords=self.level.get_bonus_coords(), collected_bonus_coords=[])

    def reset(self):
        self.state = self.get_start_state()

    def get_uncollected_bonus_coords(self):
        return list(self.state.uncollected_bonus_coords)

    def get_collected_bonus_coords(self):
        return list(self.state.collected_bonus_coords)

    def get_score(self):
        return self.state.score

    def collide(self, x, y, tile_coords):
        for tile_coord in tile_coords:
            x_overlap = tile_coord[0] < (x + self.half_player_w) and (tile_coord[0] + TILE_DIM) > (x - self.half_player_w)
            y_overlap = tile_coord[1] < (y + self.half_player_h) and (tile_coord[1] + TILE_DIM) > (y - self.half_player_h)
            if x_overlap and y_overlap:
                return tile_coord
        return None

    def next_state(self, state, action, abrv=False):
        new_state = state.clone()
        if new_state.goal_reached:
            return new_state

        # Get level bounds
        min_x, max_x = 0 + self.half_player_w, self.level.get_width() - self.half_player_w
        min_y, max_y = 0 + self.half_player_h, self.level.get_height() - self.half_player_h

        dx, dy = 0, 0
        if action.direction == ActionMaze.NORTH:
            dy = -TILE_DIM
        elif action.direction == ActionMaze.SOUTH:
            dy = TILE_DIM
        elif action.direction == ActionMaze.EAST:
            dx = TILE_DIM
        elif action.direction == ActionMaze.WEST:
            dx = -TILE_DIM

        # If using abbreviated state (without bonus tile coord info)
        if abrv:
            tile_collision_coord = self.collide(new_state.x + dx, new_state.y + dy, self.level.get_platform_coords() + self.level.get_bonus_coords())
            move_off_screen = not (min_x <= new_state.x + dx <= max_x) or not (min_y <= new_state.y + dy <= max_y)
            if tile_collision_coord is None and not move_off_screen:
                new_state.x += dx
                new_state.y += dy

        # If state contains bonus tile coord tracking info
        else:
            block_tile_collision_coord = self.collide(new_state.x + dx, new_state.y + dy,
                                                      self.level.get_platform_coords() + new_state.collected_bonus_coords)
            bonus_tile_collision_coord = self.collide(new_state.x + dx, new_state.y + dy,
                                                      new_state.uncollected_bonus_coords)
            move_off_screen = not (min_x <= new_state.x + dx <= max_x) or not (min_y <= new_state.y + dy <= max_y)

            if block_tile_collision_coord is None and bonus_tile_collision_coord is None and not move_off_screen:
                new_state.x += dx
                new_state.y += dy

            if bonus_tile_collision_coord is not None:
                new_state.score += 10  # award bonus points
                new_state.uncollected_bonus_coords.remove(bonus_tile_collision_coord)  # remove from uncollected list
                new_state.collected_bonus_coords.append(bonus_tile_collision_coord)  # add to collected list

        new_state.is_start = False
        new_state.goal_reached = self.collide(new_state.x, new_state.y, self.level.get_goal_coords())

        return new_state

    def update(self, action, precomputed_graph=None, edge_actions_dict=None):

        if precomputed_graph is None or edge_actions_dict is None:
            self.state = self.next_state(self.state, action)
        else:
            action_str = action.to_str()
            state_edges = precomputed_graph.edges(self.state.to_abrv_str())
            for edge in state_edges:
                if action_str in edge_actions_dict[edge]:
                    edge_dest = edge[1]
                    self.state = StateMaze.from_abrv_str(edge_dest)
                    break
