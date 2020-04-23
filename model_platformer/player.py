from model.level import TILE_DIM
from model_platformer.state import StatePlatformer

'''
Player Model Object
'''

HALF_TURTLE_WIDTH = int(74 / 2)
HALF_TILE_WIDTH = int(TILE_DIM / 2)


class PlayerPlatformer:

    def __init__(self, img, level):
        self.gravity = 4 if level.get_game() == 'sample' else 5
        self.steps = 8 if level.get_game() == 'sample' else 10
        self.max_vel = 8 * self.gravity

        self.half_player_h = HALF_TILE_WIDTH
        self.half_player_w = HALF_TURTLE_WIDTH if img == 'turtle' else HALF_TILE_WIDTH

        self.level = level
        self.state = None
        self.reset()

    def get_start_state(self):
        start_x, start_y = self.level.get_start_coord()
        start_x += self.half_player_w
        start_y += self.half_player_h
        return StatePlatformer(x=start_x, y=start_y, movex=0, movey=self.gravity, onground=True, is_start=True,
                               goal_reached=False, score=0, uncollected_bonus_coords=self.level.get_bonus_coords(),
                               collected_bonus_coords=[])

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

    def next_state(self, state, action):
        new_state = state.clone()
        if new_state.goal_reached:
            return new_state

        # Get level bounds
        min_x, max_x = 0 + self.half_player_w, self.level.get_width() - self.half_player_w
        min_y, max_y = 0 + self.half_player_h, self.level.get_height() - self.half_player_h

        # Account for gravity
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

        # Move in x direction
        for ii in range(abs(new_state.movex)):
            old_x = new_state.x
            if new_state.movex < 0:
                new_state.x -= 1
            elif new_state.movex > 0:
                new_state.x += 1

            tile_collision_coord = self.collide(new_state.x, new_state.y,
                                                self.level.get_platform_coords() + self.level.get_bonus_coords())
            move_off_screen = new_state.x < min_x or new_state.x > max_x

            if tile_collision_coord is not None or move_off_screen:
                new_state.x = old_x
                new_state.movex = 0
                break

        new_state.onground = False

        # Move in y direction
        for jj in range(abs(new_state.movey)):
            old_y = new_state.y
            if new_state.movey < 0:
                new_state.y -= 1
            elif new_state.movey > 0:
                new_state.y += 1

            block_tile_collision_coord = self.collide(new_state.x, new_state.y, self.level.get_platform_coords() + new_state.collected_bonus_coords)
            bonus_tile_collision_coord = self.collide(new_state.x, new_state.y, new_state.uncollected_bonus_coords)
            move_off_screen = new_state.y < min_y

            if block_tile_collision_coord is not None or bonus_tile_collision_coord is not None or move_off_screen:
                new_state.y = old_y
                if new_state.movey > 0:
                    new_state.onground = True
                new_state.movey = 0

                # If bonus tile is hit from below
                if bonus_tile_collision_coord is not None and new_state.y >= bonus_tile_collision_coord[1] + TILE_DIM:
                    new_state.score += 10  # award bonus points
                    new_state.uncollected_bonus_coords.remove(bonus_tile_collision_coord)  # remove from uncollected list
                    new_state.collected_bonus_coords.append(bonus_tile_collision_coord)   # add to collected list

                break

            # Reset state if player falls off the screen (e.g. down a pit)
            if new_state.y > max_y + TILE_DIM * 10:
                return self.get_start_state()

        new_state.is_start = False

        # Check if goal reached
        goal_tile_collision_coord = self.collide(new_state.x, new_state.y, self.level.get_goal_coords())
        new_state.goal_reached = goal_tile_collision_coord is not None

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
                    self.state = StatePlatformer.from_str(edge_dest)
                    break

