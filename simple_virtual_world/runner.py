
from mesa import Agent, Model
from mesa.space import MultiGrid
import math


class RunnerAgent(Agent):
    ''' This class will represent runners in this model '''

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        # self.type = 'type1'
        self.type = self.random.choice(['type1', 'type2'])
        if self.type == 'type2':
            self.on_road = True
            self.on_trail = False
            self.on_way_home = False
            self.entrance_trail_pos = None
            self.exit_trail_pos = None
            self.ready_to_enter_trail = False
            self.ready_to_exit_trail = False
            self.start_the_trail_run = False
            self.exit_the_trail_going_home = False

        self.direction = None
        self.count = 0
        self.distance_goal = 160
        self.want_to_go_home = False  # for type 1 & TYPE 2
        self.intersection_memory = {}  # for type 1 & TYPE 2
        self.memory_on_way_home = {}  # for type 1 & TYPE 2
        self.num_intersection_from_going_home_point = 0  # for type 1 & TYPE 2
        self.road_to_dead_end = []  # for type 1 & TYPE 2
        self.getting_out_of_deadend = False  # for type 1 & TYPE 2
        self.start_from_dead_end_road = False  # for type 1
        self.mark_road_to_home_dead_end = []  # for type 1
        if self.type == 'type1':
            self.state = '_continue_forward'
        elif self.type == 'type2':
            self.state = '_decide_way_to_get_to_trail_entrance'

    def step(self):

        self.count += 1

        if self.type == 'type1':
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

        if self.type == 'type2':
            if self.state == '_decide_way_to_get_to_trail_entrance':
                self.decide_way_to_get_to_trail_entrance()
            elif self.state == '_continue_forward_type2':
                self.continue_forward_type2()
            elif self.state == '_corner_of_road':
                self.corner_of_road()
            elif self.state == '_dead_end':
                self.dead_end()
            elif self.state == '_intersection_on_trail':
                self.intersection_on_trail()
            elif self.state == '_decide_way_to_get_to_trail_exit':
                self.decide_way_to_get_to_trail_exit()
            elif self.state == '_decide_way_go_home':
                self.decide_way_go_home()

        if self.pos == self.init_position and self.count >= self.distance_goal:
            self.state = 'rest'

    def continue_forward(self):
        '''MOVING FORWARD'''
        # Initially, start with no direction
        if self.direction == None:

            # if start at a dead end, then runner memorize to mark road out of intersection
            if len(self._get_road_cell_around()) == 1:
                self.start_from_dead_end_road = True

            # if start at intersection, then create memory at that intersection
            if len(self._get_road_cell_around()) > 2:
                self.intersection_memory[self.pos] = []

            next_position = self.random.choice(self._get_road_cell_around())

            # check and update intersection memory just passed (if starts at intersection)
            if self.pos in self.intersection_memory:
                self.intersection_memory[self.pos].append(next_position)

            self._set_new_direction_place_agent(next_position)

        # THIS PART IS USED FOR TYPE 1 AND TYPE 2
        # Already having a direction and have road ahead
        elif self._get_road_cell_forward():
            next_position = self._get_road_cell_forward()
            self._set_new_direction_place_agent(next_position)

        # Runner start in a dead end road and getting out of it, then no need to to store this dead end to ignore when getting back home
        if self.getting_out_of_deadend == True and self.pos == self.init_position:
            self.getting_out_of_deadend = False
            self.start_from_dead_end_road = True

        if self.type == 'type1':
            self._check_to_change_state()

    def _check_to_change_state(self):
        # CHANGE STATE IF NECESSARY
        # facing trail, dead end
        if len(self._get_road_cell_around()) == 1:
            self.state = '_dead_end'
        # at the corner of road
        elif len(self._get_road_cell_around()) == 2 and self._get_road_cell_forward() == False:
            if self.count >= self.distance_goal and self.want_to_go_home == False:
                self.state = '_decide_way_go_home'
                self.want_to_go_home = True
                self.num_intersection_from_going_home_point += 1
            else:
                self.state = '_corner_of_road'
        # at the intersection and have to turn
        elif len(self._get_road_cell_around()) > 2:

            # STORE DEAD END ROAD if on the way getting out of it and at intersection
            if self.getting_out_of_deadend:
                self.road_to_dead_end.append(self._get_road_cell_behind())
                self.getting_out_of_deadend = False

            if self.count >= self.distance_goal:
                self.state = '_decide_way_go_home'
                self.want_to_go_home = True
                self.num_intersection_from_going_home_point += 1
            else:
                self.state = '_intersection'

            # key: intersection center cell - is not created yet
            self._set_memory_at_intersection()

    # Continue forward for type 2
    def continue_forward_type2(self):
        # At the entrance of trail, enter it
        if self.ready_to_enter_trail:
            next_position = self._get_trail_cell_around()[0]
            self.exit_trail_pos = next_position
            self.ready_to_enter_trail = False
            self.start_the_trail_run = True
            self.on_road = False
            self.on_trail = True

        # At the exit of trail, READY TO ENTERING ROAD AGAIN TO GO HOME
        elif self.ready_to_exit_trail:
            next_position = self._get_road_cell_around()[0]
            self.ready_to_exit_trail = False
            self.exit_the_trail_going_home = True
            self.on_road = True
            self.on_trail = False

        # on road, start, haven't got to trail yet (NORMAL)
        elif self.on_road:
            next_position = self._get_road_cell_forward()
        elif self.on_trail:
            next_position = self._get_trail_cell_forward()

        self._set_new_direction_place_agent(next_position)

        # Runner start in a dead end road and getting out of it, then no need to to store this dead end to ignore when getting back home
        if self.getting_out_of_deadend == True and self.pos == self.init_position:
            self.getting_out_of_deadend = False
            self.start_from_dead_end_road = True

        # at the entrance trail, about to start the trail running
        if self.pos == self.entrance_trail_pos and self.count < self.distance_goal:
            self.ready_to_enter_trail = True

        # at the exit trail, about to get on the road and go home
        if self.pos == self.exit_trail_pos and self.count >= self.distance_goal:
            self.ready_to_exit_trail = True

        self._check_to_change_state_type2()

    # Design for type 2
    def _check_to_change_state_type2(self):

        # still on road
        if self.on_road:
            if self.ready_to_enter_trail:
                self.state = '_continue_forward_type2'
            # just start going home from the entrance
            elif len(self._get_trail_cell_around()) == 1 and self.exit_the_trail_going_home:
                self.state = '_continue_forward_type2'
                self.exit_the_trail_going_home = False
            # facing dead end
            elif len(self._get_road_cell_around()) == 1:
                self.state = '_dead_end'
            # still on road
            elif len(self._get_road_cell_around()) == 2 and self._get_road_cell_forward() != False:
                self.state = '_continue_forward_type2'
            # at the corner of road
            elif len(self._get_road_cell_around()) == 2 and self._get_road_cell_forward() == False:
                self.state = '_corner_of_road'
            # at intersection on road
            elif len(self._get_road_cell_around()) > 2:

                # on way home, at intersection, need the closest way to home
                if self.count >= self.distance_goal:
                    self.state = '_decide_way_go_home'
                    # self.on_way_running = False
                    self.on_way_home = True
                    self.want_to_go_home = True
                    self.num_intersection_from_going_home_point += 1
                # on road, at intersection, need the closest way to entrance
                else:
                    self.state = '_decide_way_to_get_to_trail_entrance'

                # store the dead end road if on the way getting out of it and at intersection
                if self.getting_out_of_deadend:
                    if self._get_road_cell_behind() not in self.road_to_dead_end:
                        self.road_to_dead_end.append(
                            self._get_road_cell_behind())
                    self.getting_out_of_deadend = False

                self._set_memory_at_intersection()

        # start the trail or on trail
        elif self.on_trail:
            # READY TO ENTER ROAD TO GO BACK HOME AGAIN
            if self.ready_to_exit_trail:
                self.state = '_continue_forward_type2'

            # just start running at the trail
            elif len(self._get_trail_cell_around()) == 1 and self.start_the_trail_run:
                self.state = '_continue_forward_type2'
                self.start_the_trail_run = False
            # facing dead end
            elif len(self._get_trail_cell_around()) == 1:
                self.state = '_dead_end'
            # still on trail
            elif len(self._get_trail_cell_around()) == 2 and self._get_trail_cell_forward() != False:
                self.state = '_continue_forward_type2'
            # at the corner of trail
            elif len(self._get_trail_cell_around()) == 2 and self._get_trail_cell_forward() == False:

                # Pass the distance goal
                if self.count >= self.distance_goal and self.num_intersection_from_going_home_point == 0:
                    self.state = '_decide_way_to_get_to_trail_exit'
                    # self.on_way_running = False
                    self.on_way_home = True
                    self.want_to_go_home = True
                    self.num_intersection_from_going_home_point += 1
                # Not yet or on the way getting home already
                else:
                    self.state = '_corner_of_road'

                # at intersection on trail
            elif len(self._get_trail_cell_around()) > 2:

                # Pass the distance goal
                if self.count >= self.distance_goal:
                    self.state = '_decide_way_to_get_to_trail_exit'
                    # self.on_way_running = False
                    self.on_way_home = True
                    self.want_to_go_home = True
                    self.num_intersection_from_going_home_point += 1
                # Not yet
                else:
                    # Normally
                    self.state = '_intersection_on_trail'

                # store the dead end road if on the way getting out of it and at intersection
                if self.getting_out_of_deadend:
                    if self._get_trail_cell_behind() not in self.road_to_dead_end:
                        self.road_to_dead_end.append(
                            self._get_trail_cell_behind())
                    self.getting_out_of_deadend = False

                self._set_memory_at_intersection()

    def dead_end(self):
        ''' make a U-turn since this type of runner cannot go pass dead end (either road or trail, depend on prederences) '''

        if self.type == 'type1':
            next_position = self._get_road_cell_behind()
        elif self.type == 'type2' and self.on_road:
            next_position = self._get_road_cell_behind()
        elif self.type == 'type2' and self.on_trail:
            next_position = self._get_trail_cell_behind()

        # let runner memorize this is dead end to store infor once getting to the intersection
        self.getting_out_of_deadend = True

        # no need to memorize as a dead end road to avoid if it is road to go to exit trail
        if self.type == 'type2' and self.pos == self.exit_trail_pos:
            self.getting_out_of_deadend = False

        # set new direction and move agent
        self._set_new_direction_place_agent(next_position)

        # if start in deadend road, and going out of it, no need to store it as dead end road to avoid during running
        if self.getting_out_of_deadend == True and self.pos == self.init_position:
            self.getting_out_of_deadend = False
            self.start_from_dead_end_road = True

        # after making a U-turn, set state back to _continue_forward
        if self.type == 'type1':
            self.state = '_continue_forward'
        elif self.type == 'type2':
            self.state = '_continue_forward_type2'

    def intersection(self):
        ''' Prefer turn right, then left, if both roads have been gone, choose the one first used to enter this intersection to get out '''

        # CHOOSE PREFER ROAD: STRAIGHT, RIGHT, LEFT, THEN CHOOSE ONE FIRST USE TO ENTER INTERS.
        if self._get_road_cell_forward() and self._get_road_cell_forward() not in self.intersection_memory[self.pos]:
            next_position = self._get_road_cell_forward()
        elif self._get_road_cell_right() and (self._get_road_cell_right() not in self.intersection_memory[self.pos]):
            next_position = self._get_road_cell_right()
        elif self._get_road_cell_left() and (self._get_road_cell_left() not in self.intersection_memory[self.pos]):
            next_position = self._get_road_cell_left()
        # runner won't go to known dead end roads even if that's road lead to it home while experiencing running
        elif (self.intersection_memory[self.pos][0] not in self.road_to_dead_end) and (self.intersection_memory[self.pos][0] not in self.mark_road_to_home_dead_end):
            next_position = self.intersection_memory[self.pos][0]
        else:
            possible_steps = self._get_road_cell_around()

            # all roads have been gone, 1st road lead to dead end, then take out the behind road and choose randomly one
            if self._get_road_cell_behind() != self.intersection_memory[self.pos][0]:
                possible_steps.remove(self._get_road_cell_behind())
            possible_steps.remove(self.intersection_memory[self.pos][0])

            next_position = self.random.choice(possible_steps)

        # set new direction and move agent
        self._set_new_direction_place_agent(next_position)

        # check and update intersection memory that has been passed
        self._set_memory_over_intersection_one_step()

        # after making a turn, set state back to _continue_forward
        self.state = '_continue_forward'

    def decide_way_go_home(self):
        ''' Try to direct runner to home as close as possible '''

        # Find prefer direction based on the 2 position (currrent and initial)
        direction = self._check_direction_of_point(
            self.pos, self.init_position)
        road_cells = self._get_road_cell_around()
        prefer_roads = []

        # set a prefer roads list to take consideration
        self._set_prefer_roads(prefer_roads, direction, road_cells)

        # choose a road randomly from the prefer road, if don't have prefer road, choose one of the other non-prefer roads
        # without considering roads leading to dead end and road just passed

        # remove roads leading to dead_end but not home
        if len(self.road_to_dead_end) > 0:
            for cell in self.road_to_dead_end:
                if cell in prefer_roads:
                    prefer_roads.remove(cell)
                if cell in road_cells:
                    road_cells.remove(cell)

        road_consider = road_cells.copy()

        # remove roads that has used to try to get home before, but didn't lead home and direct back to this intersection
        if self.pos in self.memory_on_way_home:
            for cell in self.memory_on_way_home[self.pos]:
                if cell in prefer_roads:
                    prefer_roads.remove(cell)
                if cell in road_consider:
                    road_consider.remove(cell)

        if len(prefer_roads) > 0:
            next_position = self.random.choice(prefer_roads)
            # print('CHOOSE: ', next_position)
        elif len(road_consider) > 0:
            next_position = self.random.choice(road_consider)
        elif len(road_cells) > 0:
            next_position = self.random.choice(road_cells)

        # place agent, set new direction, change state
        self._set_new_direction_place_agent(next_position)

        # check and update intersection memory that has been passed
        self._set_memory_over_intersection_one_step()

        if self.type == 'type1':
            self.state = '_continue_forward'
        elif self.type == 'type2':
            self.state = '_continue_forward_type2'

    def intersection_on_trail(self):
        # CHOOSE PREFER TRAIL: STRAIGHT, RIGHT, LEFT, THEN CHOOSE ONE FIRST USE TO ENTER INTERS
        if self._get_trail_cell_forward() and self._get_trail_cell_forward() not in self.intersection_memory[self.pos]:
            next_position = self._get_trail_cell_forward()
        elif self._get_trail_cell_right() and (self._get_trail_cell_right() not in self.intersection_memory[self.pos]):
            next_position = self._get_trail_cell_right()
        elif self._get_trail_cell_left() and (self._get_trail_cell_left() not in self.intersection_memory[self.pos]):
            next_position = self._get_trail_cell_left()
        else:
            possible_steps = self._get_trail_cell_around()
            possible_steps.remove(self._get_trail_cell_behind())

            next_position = self.random.choice(possible_steps)

        # set new direction and move agent
        self._set_new_direction_place_agent(next_position)

        # check and update intersection memory that has been passed
        self._set_memory_over_intersection_one_step()

        # after making a turn, set state back to _continue_forward
        self.state = '_continue_forward_type2'
        # print(self.intersection_memory)

    def _set_prefer_roads(self, prefer_roads, direction, type_cell_list):
        # append prefer road based on the direction toward init pos
        if direction == 'up':
            if self._get_cell('up') in type_cell_list:
                prefer_roads.append(self._get_cell('up'))
        elif direction == 'up_right':
            if self._get_cell('up') in type_cell_list:
                prefer_roads.append(self._get_cell('up'))
            if self._get_cell('right') in type_cell_list:
                prefer_roads.append(self._get_cell('right'))
        elif direction == 'right':
            if self._get_cell('right') in type_cell_list:
                prefer_roads.append(self._get_cell('right'))
        elif direction == 'down_right':
            if self._get_cell('down') in type_cell_list:
                prefer_roads.append(self._get_cell('down'))
            if self._get_cell('right') in type_cell_list:
                prefer_roads.append(self._get_cell('right'))
        elif direction == 'down':
            if self._get_cell('down') in type_cell_list:
                prefer_roads.append(self._get_cell('down'))
        elif direction == 'down_left':
            if self._get_cell('down') in type_cell_list:
                prefer_roads.append(self._get_cell('down'))
            if self._get_cell('left') in type_cell_list:
                prefer_roads.append(self._get_cell('left'))
        elif direction == 'left':
            if self._get_cell('left') in type_cell_list:
                prefer_roads.append(self._get_cell('left'))
        elif direction == 'up_left':
            if self._get_cell('up') in type_cell_list:
                prefer_roads.append(self._get_cell('up'))
            if self._get_cell('left') in type_cell_list:
                prefer_roads.append(self._get_cell('left'))

    def corner_of_road(self):
        ''' Have to turn at the corner of road '''

        # corner for type 1
        if self.type == 'type1':
            possible_steps = self._get_road_cell_around()
            possible_steps.remove(self._get_road_cell_behind())

        # corner for type 2 - on road or on trail
        elif self.type == 'type2' and self.on_road:
            possible_steps = self._get_road_cell_around()
            possible_steps.remove(self._get_road_cell_behind())
        elif self.type == 'type2' and self.on_trail:
            possible_steps = self._get_trail_cell_around()
            possible_steps.remove(self._get_trail_cell_behind())

        next_position = possible_steps[0]
        # set new direction and move agent
        self._set_new_direction_place_agent(next_position)
        # after making a turn, keep the same state if still in another corner, or set state back to _continue_forward
        if len(self._get_road_cell_around()) == 2 and (not self._check_cell_is_road(self._get_road_cell_forward()) or (self.type == 'type2' and self.on_trail and not self._check_cell_is_trail(self._get_trail_cell_forward()))):
            pass
        elif self.type == 'type1':
            self.state = '_continue_forward'
        elif self.type == 'type2':
            self.state = '_continue_forward_type2'

    def decide_way_to_get_to_trail_entrance(self):
        ''' Making a decision to get to the closest trail as soon as it can '''
        # Select the closest entrance trail
        if self.entrance_trail_pos == None:
            self.entrance_trail_pos = self._select_closest_trail()

            # set memory if start at an intersection
            if len(self._get_road_cell_around()) > 2:
                self.intersection_memory[self.pos] = []

        x, y = self.pos

        # Start at entrance trail (rare case but possible)
        if self.pos == self.entrance_trail_pos:
            self.ready_to_enter_trail = True

        # Otherwise, do normal
        else:

            if self.entrance_trail_pos == (3, 32):
                if x == 3 and y < 32:
                    self.target_point = (3, 32)
                else:
                    self.target_point = (3, 20)
            if self.entrance_trail_pos == (30, 40):
                if y == 40 and x > 29 and x < 36:
                    self.target_point = (30, 40)
                else:
                    self.target_point = (35, 40)

            direction = self._check_direction_of_point(
                self.pos, self.target_point)
            road_cells = self._get_road_cell_around()
            prefer_roads = []

            # set a prefer roads list to take consideration
            self._set_prefer_roads(prefer_roads, direction, road_cells)

            # remove roads leading to dead_end but not entrance
            if len(self.road_to_dead_end) > 0:
                for cell in self.road_to_dead_end:
                    if cell in prefer_roads:
                        prefer_roads.remove(cell)
                    if cell in road_cells:
                        road_cells.remove(cell)

            road_consider = road_cells.copy()

            # remove roads that has used before, but didn't lead to anywhere
            if self.pos in self.intersection_memory:
                for cell in self.intersection_memory[self.pos]:
                    if cell in prefer_roads:
                        prefer_roads.remove(cell)
                    if cell in road_consider:
                        road_consider.remove(cell)

            if len(prefer_roads) > 0:
                next_position = self.random.choice(prefer_roads)
            elif len(road_consider) > 0:
                next_position = self.random.choice(road_consider)
            elif len(road_cells) > 0:
                next_position = self.random.choice(road_cells)

            # place agent, set new direction, change state
            self._set_new_direction_place_agent(next_position)

        # get to entrance trail at step 2 (rare case but possible)
        if self.pos == self.entrance_trail_pos:
            self.ready_to_enter_trail = True

        # check and update intersection memory that has been passed
        self._set_memory_over_intersection_one_step()

        self._check_to_change_state_type2()

    def decide_way_to_get_to_trail_exit(self):
        ''' Making a decision to get to trail exit as soon as it can '''

        x, y = self.pos

        # Otherwise, do normal
        if True:

            direction = self._check_direction_of_point(
                self.pos, self.exit_trail_pos)
            trail_cells = self._get_trail_cell_around()
            prefer_trails = []

            # set a prefer roads list to take consideration
            self._set_prefer_roads(prefer_trails, direction, trail_cells)

            # remove roads leading to dead_end but not exit or entrance
            if len(self.road_to_dead_end) > 0:
                for cell in self.road_to_dead_end:
                    if cell in prefer_trails:
                        prefer_trails.remove(cell)
                    if cell in trail_cells:
                        trail_cells.remove(cell)

            trail_consider = trail_cells.copy()

            # remove roads that has used before, but didn't lead to anywhere
            if self.pos in self.memory_on_way_home:
                for cell in self.memory_on_way_home[self.pos]:
                    if cell in prefer_trails:
                        prefer_trails.remove(cell)
                    if cell in trail_consider:
                        trail_consider.remove(cell)

            # print('PREFER ROAD: ', prefer_trails)

            if len(prefer_trails) > 0:
                next_position = self.random.choice(prefer_trails)
            # consider roads with that no dead end, no road used before
            elif len(trail_consider) > 0:
                next_position = self.random.choice(trail_consider)
            # consider roads including roads have been used before
            elif len(trail_cells) > 0:
                next_position = self.random.choice(trail_cells)

            # place agent, set new direction, change state
            self._set_new_direction_place_agent(next_position)

        # check and update intersection memory that has been passed
        self._set_memory_over_intersection_one_step()

        self._check_to_change_state_type2()

    def _select_closest_trail(self):
        ''' Estimate roughly the distance between 2 points and return the closest entrance point '''
        x, y = self.pos

        min_distance = None
        for entrance_pos in self.model.trail_entrance_point:
            a, b = entrance_pos
            estimate_distance = math.sqrt((x - a)**2 + (y - b)**2)
            if min_distance == None or (estimate_distance < min_distance):
                min_distance = estimate_distance
                prefer_entrance = entrance_pos

        return prefer_entrance

    def _set_memory_at_intersection(self):
        # create a key as the intersection center cell if it's created yet, then append road cell passed
        if self.pos not in self.intersection_memory:
            self.intersection_memory[self.pos] = []
        if self._get_road_cell_behind() not in self.intersection_memory[self.pos]:
            self.intersection_memory[self.pos].append(
                self._get_road_cell_behind())

        # FOR TYPE 1 & TYPE 2
        # on the way home memory
        if self.want_to_go_home:
            if self.pos not in self.memory_on_way_home:
                self.memory_on_way_home[self.pos] = []
            # no need to store road behind as memory gone home, if the step got to intersection just reaches the exact distance goal
            # so it can consider the road behind as one of the nearest ways to get back to home
            if self.num_intersection_from_going_home_point > 1 and (self._get_road_cell_behind() not in self.memory_on_way_home[self.pos]):
                self.memory_on_way_home[self.pos].append(
                    self._get_road_cell_behind())

        # FOR TYPE 1
        # mark the road the lead to home in the dead end road
        if self.start_from_dead_end_road:
            if len(self.mark_road_to_home_dead_end) == 0:
                self.mark_road_to_home_dead_end.append(
                    self._get_road_cell_behind())

    def _set_memory_over_intersection_one_step(self):
        # store the road cell over the intersection one step
        if self._get_road_cell_behind() in self.intersection_memory:
            if self.pos not in self.intersection_memory[self._get_road_cell_behind()]:
                self.intersection_memory[self._get_road_cell_behind()].append(
                    self.pos)

        # FOR TYPE 1
        # on the way home memory
        if self.want_to_go_home:
            if self._get_road_cell_behind() in self.memory_on_way_home:
                if self.pos not in self.memory_on_way_home[self._get_road_cell_behind()]:
                    self.memory_on_way_home[self._get_road_cell_behind()].append(
                        self.pos)

    def _set_new_direction_place_agent(self, next_pos):
        # Unpack tuple position
        x, y = self.pos
        a, b = next_pos

        # Update heatmap for everytime it goes to new location
        self.model.heatmap_data[self.model.height - 1 - y][x] += 1
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

    # ROAD
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

    # TRAIL
    def _get_trail_cell_around(self):
        # List contains position of 4 cells around (top, bottom, left, right)
        cells_around = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False)
        # List contains position of road cells that are from those 4 cells above
        possible_trails = []
        for pos in cells_around:
            for cell_object in self.model.background_cells:
                if cell_object.pos == pos and cell_object.type == 'trail':
                    possible_trails.append(pos)
        return possible_trails

    def _get_trail_cell_behind(self):
        if self.direction == 'right':
            return (self.pos[0] - 1, self.pos[1])
        elif self.direction == 'left':
            return (self.pos[0] + 1, self.pos[1])
        elif self.direction == 'up':
            return (self.pos[0], self.pos[1] - 1)
        elif self.direction == 'down':
            return (self.pos[0], self.pos[1] + 1)

    def _get_trail_cell_forward(self):
        if self.direction == 'right' and self._check_cell_is_trail((self.pos[0] + 1, self.pos[1])):
            return (self.pos[0] + 1, self.pos[1])
        elif self.direction == 'left' and self._check_cell_is_trail((self.pos[0] - 1, self.pos[1])):
            return (self.pos[0] - 1, self.pos[1])
        elif self.direction == 'up' and self._check_cell_is_trail((self.pos[0], self.pos[1] + 1)):
            return (self.pos[0], self.pos[1] + 1)
        elif self.direction == 'down' and self._check_cell_is_trail((self.pos[0], self.pos[1] - 1)):
            return (self.pos[0], self.pos[1] - 1)
        else:
            return False

    def _get_trail_cell_right(self):
        if self.direction == 'right' and self._check_cell_is_trail((self.pos[0], self.pos[1] - 1)):
            return (self.pos[0], self.pos[1] - 1)
        elif self.direction == 'left' and self._check_cell_is_trail((self.pos[0], self.pos[1] + 1)):
            return (self.pos[0], self.pos[1] + 1)
        elif self.direction == 'up' and self._check_cell_is_trail((self.pos[0] + 1, self.pos[1])):
            return (self.pos[0] + 1, self.pos[1])
        elif self.direction == 'down' and self._check_cell_is_trail((self.pos[0] - 1, self.pos[1])):
            return (self.pos[0] - 1, self.pos[1])
        else:
            return False

    def _get_trail_cell_left(self):
        if self.direction == 'right' and self._check_cell_is_trail((self.pos[0], self.pos[1] + 1)):
            return (self.pos[0], self.pos[1] + 1)
        elif self.direction == 'left' and self._check_cell_is_trail((self.pos[0], self.pos[1] - 1)):
            return (self.pos[0], self.pos[1] - 1)
        elif self.direction == 'up' and self._check_cell_is_trail((self.pos[0] - 1, self.pos[1])):
            return (self.pos[0] - 1, self.pos[1])
        elif self.direction == 'down' and self._check_cell_is_trail((self.pos[0] + 1, self.pos[1])):
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

    def _check_cell_is_trail(self, cell_position):
        possible_trails = self._get_trail_cell_around()
        if cell_position in possible_trails:
            return True
        else:
            return False

    def _check_direction_of_point(self, current_pos, target_position):
        x, y = current_pos
        a, b = target_position

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
