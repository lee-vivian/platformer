from model.level import TILE_DIM
from model.metatile import Metatile
from model_platformer.state import StatePlatformer

from utils import list_to_dict

'''
Player Model Object
'''

HALF_TURTLE_WIDTH = int(74 / 2)
HALF_TILE_WIDTH = int(TILE_DIM / 2)


class PlayerPlatformer:

    def __init__(self, img, level):
        self.gravity = 4 if level.get_game() == 'sample' else 5
        self.steps = 8 if level.get_game() == 'sample' else 10
        self.max_vel = 7 * self.gravity if level.get_game() == 'kid_icarus' else 8 * self.gravity

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
                               goal_reached=False, hit_bonus_coord=None, is_dead=False)

    def reset(self):
        self.state = self.get_start_state()

    def is_dead(self):
        return self.state.is_dead

    def goal_reached(self):
        return self.state.goal_reached

    def get_hit_bonus_coord(self):
        return self.state.hit_bonus_coord

    def collide(self, x, y, tile_coords):
        for tile_coord in tile_coords:
            x_overlap = tile_coord[0] < (x + self.half_player_w) and (tile_coord[0] + TILE_DIM) > (x - self.half_player_w)
            y_overlap = tile_coord[1] < (y + self.half_player_h) and (tile_coord[1] + TILE_DIM) > (y - self.half_player_h)
            if x_overlap and y_overlap:
                return tile_coord
        return None

    def next_state(self, state, action):
        new_state = state.clone()
        if new_state.goal_reached or new_state.is_dead:
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

        use_kid_icarus_rules = self.level.get_game() == "kid_icarus"
        tile_coord_dict = list_to_dict(self.level.get_platform_coords() +
                                       self.level.get_bonus_coords())

        # Move in x direction
        for ii in range(abs(new_state.movex)):
            old_x = new_state.x
            if new_state.movex < 0:
                new_state.x -= 1
            elif new_state.movex > 0:
                new_state.x += 1

            # Handle block tile collisions
            tile_collision_coord = self.collide(new_state.x, new_state.y,
                                                self.level.get_platform_coords() +
                                                self.level.get_bonus_coords())

            # Handle moving off the screen
            move_off_screen_left = new_state.x < min_x
            move_off_screen_right = new_state.x > max_x
            move_off_screen_x = move_off_screen_left or move_off_screen_right

            if use_kid_icarus_rules and move_off_screen_x:

                # Wrap around to other side
                new_state.x = max_x if move_off_screen_left else min_x
                current_occupied_tile_coord = Metatile.get_metatile_coord_from_state_coord((new_state.x, new_state.y), TILE_DIM)

                # Revert to old x position if tile blocks path to the other side
                if tile_coord_dict.get(current_occupied_tile_coord) is not None:
                    new_state.x = old_x
                    new_state.movex = 0
                    break

            if (move_off_screen_x and not use_kid_icarus_rules) or tile_collision_coord is not None:
                new_state.x = old_x
                new_state.movex = 0
                break

        new_state.onground = False
        new_state.hit_bonus_coord = None

        # Move in y direction
        for jj in range(abs(new_state.movey)):
            old_y = new_state.y
            if new_state.movey < 0:
                new_state.y -= 1
            elif new_state.movey > 0:
                new_state.y += 1

            # Collide with one-way block tile from above
            one_way_block_tile_collision_coord = self.collide(new_state.x, new_state.y, self.level.get_one_way_platform_coords())
            hit_one_way_block_tile_from_above = one_way_block_tile_collision_coord is not None and new_state.movey > 0 and old_y + self.half_player_h <= one_way_block_tile_collision_coord[1]

            block_tile_collision_coord = self.collide(new_state.x, new_state.y, self.level.get_platform_coords())
            bonus_tile_collision_coord = self.collide(new_state.x, new_state.y, self.level.get_bonus_coords())
            collide = block_tile_collision_coord is not None or bonus_tile_collision_coord is not None or hit_one_way_block_tile_from_above
            move_off_screen_y = new_state.y < min_y

            if collide or move_off_screen_y:
                new_state.y = old_y
                new_state.onground = new_state.movey > 0
                new_state.movey = 0

                # if bonus tile was hit from below
                if bonus_tile_collision_coord is not None and new_state.y >= bonus_tile_collision_coord[1] + TILE_DIM:
                    new_state.hit_bonus_coord = bonus_tile_collision_coord

            # Player is dead if it falls off the screen (e.g. down a pit)
            if new_state.y > max_y + TILE_DIM * 10:
                new_state.is_dead = True
                break

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

