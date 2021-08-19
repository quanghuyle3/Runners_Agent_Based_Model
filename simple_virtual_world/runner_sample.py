from mesa import Agent, Model
from mesa.space import MultiGrid


class RunnerAgent(Agent):
    ''' This class will represent runners in this model '''

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = 'runner'
        self.direction = None
        self.count = 0
        self.distance_goal = 100
        self.want_to_go_home = True
        # {(x,y):[(),(),(),..]
        self.intersection_memory = {}
        self.road_to_dead_end = []
        self.getting_out_of_deadend = False
        self.state = '_continue_forward'

    def step(self):

        if self.state == '_continue_forward':
            self.continue_forward()
        elif self.state == '_intersection':
            self.intersection()
        elif self.state == '_corner_of_road':
            self.corner_of_road()
        elif self.state == '_dead_end':
            self.dead_end()
        elif self.state == '_decide_way_go_home':
            self.decide_way_go_home()

        elif self.state == 'rest':
            pass

        self.count += 1

        if self.pos == self.init_position and self.count >= self.distance_goal:
            self.state = 'rest'
            print('FINISH')

    def continue_forward(self):
        '''MOVING FORWARD'''
        # Initially, start with no direction
        if self.direction == None:

            # if start at a dead end, then runner memorize and set memory once get to intersection
            if len(self._get_road_cell_around()) == 1:
                self.getting_out_of_deadend = True
            # if start at intersection, then create memory at that intersection
            if len(self._get_road_cell_around()) > 2:
                self.intersection_memory[self.pos] = []

            next_position = self.random.choice(self._get_road_cell_around())

            # check and update intersection memory just passed
            if self.pos in self.intersection_memory:
                self.intersection_memory[self.pos].append(next_position)

            self._set_new_direction_place_agent(next_position)

        # Already having a direction and have road ahead
        elif self._get_road_cell_forward():
            next_position = self._get_road_cell_forward()
            self._set_new_direction_place_agent(next_position)

        # CHANGE STATE IF NECESSARY
        # facing trail, dead end
        if len(self._get_road_cell_around()) == 1:
            print('CHANGE STATE 1')
            self.state = '_dead_end'
        # at the corner of road
        elif len(self._get_road_cell_around()) == 2 and self._get_road_cell_forward() == False:
            print('CHANGE STATE 2')
            self.state = '_corner_of_road'
        # at the intersection and have to turn
        elif len(self._get_road_cell_around()) > 2:
            print('CHANGE STATE 3')
            # key: intersection center cell - is not created yet
            self._set_memory_at_intersection()
            if self.count >= self.distance_goal:
                print('FIND WAY HOME')
                self.state = '_decide_way_go_home'
                self.want_to_go_home = True
            else:
                self.state = '_intersection'

    def dead_end(self):
        ''' make a U-turn since this type of runner avoids trail, also avoid dead end '''

        next_position = self._get_road_cell_behind()
        print('U TURN: ', next_position)
        # let runner memorize this is dead end to store infor once getting to the intersection
        self.getting_out_of_deadend = True
        # set new direction and move agent
        self._set_new_direction_place_agent(next_position)
        # after making a U-turn, set state back to _continue_forward
        self.state = '_continue_forward'

    def intersection(self):
        ''' Prefer turn right, then left, if both roads have been gone, choose the one first used to enter this intersection to get out '''

        # store the dead end road if on the way getting out of it
        if self.getting_out_of_deadend:
            self.road_to_dead_end.append(self._get_road_cell_behind())
            self.getting_out_of_deadend = False

        # CHOOSE PREFER ROAD: STRAIGHT, RIGHT, LEFT, THEN CHOOSE ONE FIRST USE TO ENTER INTERS.
        if self._get_road_cell_forward() and self._get_road_cell_forward() not in self.intersection_memory[self.pos]:
            next_position = self._get_road_cell_forward()
        elif self._get_road_cell_right() and (self._get_road_cell_right() not in self.intersection_memory[self.pos]):
            next_position = self._get_road_cell_right()
        elif self._get_road_cell_left() and (self._get_road_cell_left() not in self.intersection_memory[self.pos]):
            next_position = self._get_road_cell_left()
        else:
            next_position = self.intersection_memory[self.pos][0]

        # check and update intersection memory just passed
        if next_position not in self.intersection_memory[self.pos]:
            self.intersection_memory[self.pos].append(next_position)

        # set new direction and move agent
        self._set_new_direction_place_agent(next_position)
        # after making a turn, set state back to _continue_forward
        self.state = '_continue_forward'
        print(self.intersection_memory)

    def decide_way_go_home(self):
        ''' Try to direct runner to home as close as possible '''
        # x, y = self.pos

        # Find prefer direction based on the 2 position (currrent and initial)
        direction = self._check_direction_of_point(
            self.pos, self.init_position)
        road_cells = self._get_road_cell_around()
        print('ROAD CELLS: ', road_cells)
        prefer_roads = []

        # append prefer road based on the direction toward init pos
        if direction == 'up':
            if self._get_cell('up') in road_cells:
                prefer_roads.append(self._get_cell('up'))
        elif direction == 'up_right':
            if self._get_cell('up') in road_cells:
                prefer_roads.append(self._get_cell('up'))
            if self._get_cell('right') in road_cells:
                prefer_roads.append(self._get_cell('right'))
        elif direction == 'right':
            if self._get_cell('right') in road_cells:
                prefer_roads.append(self._get_cell('right'))
        elif direction == 'down_right':
            if self._get_cell('down') in road_cells:
                prefer_roads.append(self._get_cell('down'))
            if self._get_cell('right') in road_cells:
                prefer_roads.append(self._get_cell('right'))
        elif direction == 'down':
            if self._get_cell('down') in road_cells:
                prefer_roads.append(self._get_cell('down'))
        elif direction == 'down_left':
            if self._get_cell('down') in road_cells:
                prefer_roads.append(self._get_cell('down'))
            if self._get_cell('left') in road_cells:
                prefer_roads.append(self._get_cell('left'))
        elif direction == 'left':
            if self._get_cell('left') in road_cells:
                prefer_roads.append(self._get_cell('left'))
        elif direction == 'up_left':
            if self._get_cell('up') in road_cells:
                prefer_roads.append(self._get_cell('up'))
            if self._get_cell('left') in road_cells:
                prefer_roads.append(self._get_cell('left'))

        # choose a road randomly from the prefer road, if don't have prefer road, choose one of the other non-prefer roads
        # without considering roads leading to dead end
        print(direction)
        print('PREFER ROAD: ', prefer_roads)

        if len(self.road_to_dead_end) > 0:
            for cell in self.road_to_dead_end:
                if cell in prefer_roads:
                    prefer_roads.remove(cell)
                if cell in road_cells:
                    road_cells.remove(cell)

        if len(prefer_roads) > 0:
            next_position = self.random.choice(prefer_roads)
            print('CHOOSE: ', next_position)
        else:
            next_position = self.random.choice(road_cells)

        # place agent, set new direction, change state
        self._set_new_direction_place_agent(next_position)
        self.state = '_continue_forward'

    def corner_of_road(self):
        ''' Have to turn at the corner of road '''

        possible_steps = self._get_road_cell_around()
        possible_steps.remove(self._get_road_cell_behind())

        next_position = possible_steps[0]
        print(next_position)
        # set new direction and move agent
        self._set_new_direction_place_agent(next_position)
        # after making a turn, set state back to _continue_forward
        self.state = '_continue_forward'

    def _set_memory_at_intersection(self):
        # create a key as the intersection center cell if it's created yet, then append road cell passed
        if self.pos not in self.intersection_memory:
            self.intersection_memory[self.pos] = []
        if self._get_road_cell_behind() not in self.intersection_memory[self.pos]:
            self.intersection_memory[self.pos].append(
                self._get_road_cell_behind())

    def _set_new_direction_place_agent(self, next_pos):
        # Unpack tuple position
        x, y = self.pos
        a, b = next_pos
        # Set new direction
        if a > x:
            self.direction = 'right'
        elif a < x:
            self.direction = 'left'
        elif b > y:
            self.direction = 'up'
        else:
            self.direction = 'down'
        # Place agent to new position
        self.model.grid.move_agent(self, next_pos)

    def _get_road_cell_around(self):
        # List contains position of 4 cells around (top, bottom, left, right)
        cells_around = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False)
        # List contains position of road cells that are from those 4 cells above
        possible_roads = []
        for pos in cells_around:
            # x, y = pos
            for cell_object in self.model.background_cells:
                if cell_object.pos == pos and cell_object.type == 'road':
                    possible_roads.append(pos)
        return possible_roads

    def _get_road_cell_behind(self):
        if self.direction == 'right':
            return (self.pos[0] - 1, self.pos[1])
        elif self.direction == 'left':
            return (self.pos[0] + 1, self.pos[1])
        elif self.direction == 'up':
            return (self.pos[0], self.pos[1] - 1)
        elif self.direction == 'down':
            return (self.pos[0], self.pos[1] + 1)

    def _get_road_cell_forward(self):
        if self.direction == 'right' and self._check_cell_is_road((self.pos[0] + 1, self.pos[1])):
            return (self.pos[0] + 1, self.pos[1])
        elif self.direction == 'left' and self._check_cell_is_road((self.pos[0] - 1, self.pos[1])):
            return (self.pos[0] - 1, self.pos[1])
        elif self.direction == 'up' and self._check_cell_is_road((self.pos[0], self.pos[1] + 1)):
            return (self.pos[0], self.pos[1] + 1)
        elif self.direction == 'down' and self._check_cell_is_road((self.pos[0], self.pos[1] - 1)):
            return (self.pos[0], self.pos[1] - 1)
        else:
            return False

    def _get_road_cell_right(self):
        if self.direction == 'right' and self._check_cell_is_road((self.pos[0], self.pos[1] - 1)):
            return (self.pos[0], self.pos[1] - 1)
        elif self.direction == 'left' and self._check_cell_is_road((self.pos[0], self.pos[1] + 1)):
            return (self.pos[0], self.pos[1] + 1)
        elif self.direction == 'up' and self._check_cell_is_road((self.pos[0] + 1, self.pos[1])):
            return (self.pos[0] + 1, self.pos[1])
        elif self.direction == 'down' and self._check_cell_is_road((self.pos[0] - 1, self.pos[1])):
            return (self.pos[0] - 1, self.pos[1])
        else:
            return False

    def _get_road_cell_left(self):
        if self.direction == 'right' and self._check_cell_is_road((self.pos[0], self.pos[1] + 1)):
            return (self.pos[0], self.pos[1] + 1)
        elif self.direction == 'left' and self._check_cell_is_road((self.pos[0], self.pos[1] - 1)):
            return (self.pos[0], self.pos[1] - 1)
        elif self.direction == 'up' and self._check_cell_is_road((self.pos[0] - 1, self.pos[1])):
            return (self.pos[0] - 1, self.pos[1])
        elif self.direction == 'down' and self._check_cell_is_road((self.pos[0] + 1, self.pos[1])):
            return (self.pos[0] + 1, self.pos[1])
        else:
            return False

    def _get_cell(self, type):
        x, y = self.pos
        if type == 'up':
            return (x, y + 1)
        elif type == 'down':
            return (x, y - 1)
        elif type == 'left':
            return (x - 1, y)
        elif type == 'right':
            return (x + 1, y)

    def _check_cell_is_road(self, cell_position):
        possible_roads = self._get_road_cell_around()
        if cell_position in possible_roads:
            return True
        else:
            return False

    def _check_direction_of_point(self, current_pos, init_position):
        x, y = current_pos
        a, b = init_position

        distance_x = a - x
        distance_y = b - y

        if distance_y > 0 and distance_x == 0:
            return 'up'
        elif distance_y > 0 and distance_x > 0:
            return 'up_right'
        elif distance_y == 0 and distance_x > 0:
            return 'right'
        elif distance_y < 0 and distance_x > 0:
            return 'down_right'
        elif distance_y < 0 and distance_x == 0:
            return 'down'
        elif distance_y < 0 and distance_x < 0:
            return 'down_left'
        elif distance_y == 0 and distance_x < 0:
            return 'left'
        elif distance_y > 0 and distance_x < 0:
            return 'up_left'
