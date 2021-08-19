from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation


class RunnerAgent(Agent):
    ''' This class will represent runners in this model '''

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = 'runner'
        self.direction = None
        self.count = 0
        # {(x,y):[(),(),(),..]
        self.intersection_memory = {}
        self.state = 'run'

    def step(self):

        if self.state == 'run':
            self.go_forward()

    def go_forward(self):
        # List contains position of 4 cells around (top, bottom, left, right)
        cells_around = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False)
        # List contains position of road cells that are from those 4 cells above
        possible_steps = []
        for pos in cells_around:
            # x, y = pos
            for cell_object in self.model.background_cells:
                if cell_object.pos == pos and cell_object.type == 'road':
                    possible_steps.append(pos)

        # Runner has to choose a direction at first
        if self.direction == None:
            next_position = self.random.choice(possible_steps)

        # Runner already had a direction
        else:
            x, y = self.pos     # unpack current position

            # In the right (east) direction
            if self.direction == 'right':

                # continue forward if having road and that road haven't been gone through
                if (((x + 1, y) in possible_steps) and (self.pos not in self.intersection_memory)) or (((x + 1, y) in possible_steps) and (self.pos in self.intersection_memory) and ((x + 1, y) not in self.intersection_memory[self.pos])):
                    next_position = (x + 1, y)
                    # At the intersection, or over the center 1 cell, store a center cell, and the cells around that have been gone through
                    if len(possible_steps) > 2:
                        # create key-value inside
                        if self.pos not in self.intersection_memory:
                            # key: center cell's position, value: list of around road cells position that have been gone through
                            self.intersection_memory[self.pos] = []

                        self.intersection_memory[self.pos].append((x - 1, y))

                    # Append the current pos once passed the intersection
                    elif (self.pos[0] - 1, self.pos[1]) in self.intersection_memory:
                        self.intersection_memory[(
                            self.pos[0] - 1, self.pos[1])].append(self.pos)

                # either one-way road or at the intersection that runner must turn
                else:
                    # facing trail or dead end --> make a U-turn
                    if len(possible_steps) == 1:
                        next_position = (x - 1, y)
                    # at the corner and have to turn either left or right
                    elif len(possible_steps) == 2:
                        # remove the behind step and assign the turning road
                        possible_steps.remove((x - 1, y))
                        next_position = possible_steps[0]
                    # at intersection and have to turn and also avoid repeated route
                    else:
                        # Create key memory for that intersection if not yet created
                        if self.pos not in self.intersection_memory:
                            self.intersection_memory[self.pos] = []
                        # Prefer turn right first
                        if ((x, y - 1) in possible_steps) and ((x, y - 1) not in self.intersection_memory[self.pos]):
                            next_position = (x, y - 1)
                            # append the cell behind which just passed through before entering this center
                            self.intersection_memory[self.pos].append(
                                (x - 1, y))
                        # Turn left instead if already turned right
                        elif ((x, y + 1) in possible_steps) and (x, y + 1) not in self.intersection_memory[self.pos]:
                            next_position = (x, y + 1)
                            # append the cell behind which just passed through before entering this center
                            self.intersection_memory[self.pos].append(
                                (x - 1, y))
                        # Choose the first route that the runner used to enter this intersection to get out of this loop
                        else:
                            num_routes = len(
                                self.intersection_memory[self.pos])
                            for i in range(num_routes - 1):
                                self.intersection_memory[self.pos].pop()
                            # set position by the remained position (first route)
                            next_position = self.intersection_memory[self.pos][0]

            # In the left (west) direction
            elif self.direction == 'left':

                # continue forward if having road and that road haven't been gone through
                if (((x - 1, y) in possible_steps) and (self.pos not in self.intersection_memory)) or (((x - 1, y) in possible_steps) and (self.pos in self.intersection_memory) and ((x - 1, y) not in self.intersection_memory[self.pos])):
                    next_position = (x - 1, y)
                    # At the intersection, or over the center 1 cell, store a center cell, and the cells around that have been gone through
                    if len(possible_steps) > 2:
                        # create key-value inside
                        if self.pos not in self.intersection_memory:
                            # key: center cell's position, value: list of around road cells position that have been gone through
                            self.intersection_memory[self.pos] = []

                        self.intersection_memory[self.pos].append((x + 1, y))

                    # Append the current pos once passed the intersection
                    elif (self.pos[0] + 1, self.pos[1]) in self.intersection_memory:
                        self.intersection_memory[(
                            self.pos[0] + 1, self.pos[1])].append(self.pos)

                # either one-way road or at the intersection that runner must turn
                else:
                    # facing trail or dead end --> make a U-turn
                    if len(possible_steps) == 1:
                        next_position = (x + 1, y)
                    # at the corner and have to turn either left or right
                    elif len(possible_steps) == 2:
                        # remove the behind step and assign the turning road
                        possible_steps.remove((x + 1, y))
                        next_position = possible_steps[0]
                    # at intersection and have to turn and also avoid repeated route
                    else:
                        # create key memory for that intersection if not yet created
                        if self.pos not in self.intersection_memory:
                            self.intersection_memory[self.pos] = []
                        # Prefer turn right first
                        if ((x, y + 1) in possible_steps) and ((x, y + 1) not in self.intersection_memory[self.pos]):
                            next_position = (x, y + 1)
                            # append the cell behind which just passed through before entering this center
                            self.intersection_memory[self.pos].append(
                                (x + 1, y))
                        # Turn left instead if already turned right
                        elif ((x, y - 1) in possible_steps) and (x, y - 1) not in self.intersection_memory[self.pos]:
                            next_position = (x, y - 1)
                            # append the cell behind which just passed through before entering this center
                            self.intersection_memory[self.pos].append(
                                (x + 1, y))
                        # choose the first route that the runner used to enter this intersection to get out of this loop
                        else:
                            num_routes = len(
                                self.intersection_memory[self.pos])
                            for i in range(num_routes - 1):
                                self.intersection_memory[self.pos].pop()
                            # set position by the remained position (first route)
                            next_position = self.intersection_memory[self.pos][0]

            # In the up (north) direction
            elif self.direction == 'up':
                # continue forward if having road and that road haven't been gone through
                if (((x, y + 1) in possible_steps) and (self.pos not in self.intersection_memory)) or (((x, y + 1) in possible_steps) and (self.pos in self.intersection_memory) and ((x, y + 1) not in self.intersection_memory[self.pos])):
                    next_position = (x, y + 1)
                    # At the intersection, or over the center 1 cell, store a center cell, and the cells around that have been gone through
                    if len(possible_steps) > 2:
                        # create key-value inside
                        if self.pos not in self.intersection_memory:
                            # key: center cell's position, value: list of around road cells position that have been gone through
                            self.intersection_memory[self.pos] = []

                        self.intersection_memory[self.pos].append((x, y - 1))

                    # Append the current pos once passed the intersection
                    elif (self.pos[0], self.pos[1] - 1) in self.intersection_memory:
                        self.intersection_memory[(
                            self.pos[0], self.pos[1] - 1)].append(self.pos)

                # either one-way road or at the intersection that runner must turn
                else:
                    # facing trail or dead end --> make a U-turn
                    if len(possible_steps) == 1:
                        next_position = (x, y - 1)
                    # at the corner and have to turn either left or right
                    elif len(possible_steps) == 2:
                        # remove the behind step and assign the turning road
                        possible_steps.remove((x, y - 1))
                        next_position = possible_steps[0]
                    # at intersection and have to turn and also avoid repeated route
                    else:
                        # create key memory for that intersection if not yet created
                        if self.pos not in self.intersection_memory:
                            self.intersection_memory[self.pos] = []
                        # Prefer turn right first
                        if ((x + 1, y) in possible_steps) and ((x + 1, y) not in self.intersection_memory[self.pos]):
                            next_position = (x + 1, y)
                            # append the cell behind which just passed through before entering this center
                            self.intersection_memory[self.pos].append(
                                (x, y - 1))
                        # Turn left instead if already turned right
                        elif ((x - 1, y) in possible_steps) and (x - 1, y) not in self.intersection_memory[self.pos]:
                            next_position = (x - 1, y)
                            # append the cell behind which just passed through before entering this center
                            self.intersection_memory[self.pos].append(
                                (x, y - 1))
                        else:   # choose the first route that the runner used to enter this intersection to get out of this loop
                            num_routes = len(
                                self.intersection_memory[self.pos])
                            for i in range(num_routes - 1):
                                self.intersection_memory[self.pos].pop()
                            # set position by the remained position (first route)
                            next_position = self.intersection_memory[self.pos][0]

            # In the down (south) direction
            elif self.direction == 'down':
                # continue forward if having road and that road haven't been gone through
                if (((x, y - 1) in possible_steps) and (self.pos not in self.intersection_memory)) or (((x, y - 1) in possible_steps) and (self.pos in self.intersection_memory) and ((x, y - 1) not in self.intersection_memory[self.pos])):
                    next_position = (x, y - 1)
                    # At the intersection, or over the center 1 cell, store a center cell, and the cells around that have been gone through
                    if len(possible_steps) > 2:
                        # create key-value inside
                        if self.pos not in self.intersection_memory:
                            # key: center cell's position, value: list of around road cells position that have been gone through
                            self.intersection_memory[self.pos] = []

                        self.intersection_memory[self.pos].append((x, y + 1))

                    # Append the current pos once passed the intersection
                    elif (self.pos[0], self.pos[1] + 1) in self.intersection_memory:
                        self.intersection_memory[(
                            self.pos[0], self.pos[1] + 1)].append(self.pos)

                # either one-way road or at the intersection that runner must turn
                else:
                    # facing trail or dead end --> make a U-turn
                    if len(possible_steps) == 1:
                        next_position = (x, y + 1)
                    # at the corner and have to turn either left or right
                    elif len(possible_steps) == 2:
                        # remove the behind step and assign the turning road
                        possible_steps.remove((x, y + 1))
                        next_position = possible_steps[0]
                    # at intersection and have to turn and also avoid repeated route
                    else:
                        # create key memory for that intersection if not yet created
                        if self.pos not in self.intersection_memory:
                            self.intersection_memory[self.pos] = []
                        # Prefer turn right first
                        if ((x - 1, y) in possible_steps) and ((x - 1, y) not in self.intersection_memory[self.pos]):
                            next_position = (x - 1, y)
                            # append the cell behind which just passed through before entering this center
                            self.intersection_memory[self.pos].append(
                                (x, y + 1))
                        # Turn left instead if already turned right
                        elif ((x + 1, y) in possible_steps) and (x + 1, y) not in self.intersection_memory[self.pos]:
                            next_position = (x + 1, y)
                            # append the cell behind which just passed through before entering this center
                            self.intersection_memory[self.pos].append(
                                (x, y + 1))
                        # choose the first route that the runner used to enter this intersection to get out of this loop
                        else:
                            num_routes = len(
                                self.intersection_memory[self.pos])
                            for i in range(num_routes - 1):
                                self.intersection_memory[self.pos].pop()
                            # set position by the remained position (first route)
                            next_position = self.intersection_memory[self.pos][0]

        # Update direction for every step
        self.direction = self.set_direction(self.pos, next_position)
        self.model.grid.move_agent(self, next_position)
        self.count += 1
        if self.pos == self.init_position:
            print('NUMBER OF STEP TO COMPLETE THIS LOOP RUN: ', self.count)

        # print(self.intersection_memory)

    def set_direction(self, current_pos, next_pos):
        # Unpack tuple position
        x, y = current_pos
        a, b = next_pos
        if a > x:
            return 'right'
        elif a < x:
            return 'left'
        elif b > y:
            return 'up'
        else:
            return 'down'


class CellAgent(Agent):
    ''' This class will represent cells in the grid
        Purpose: Create visualization for virtual map
        Also, cells will stay with same attribute, and color at the same location forever '''

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)


class VirtualWorldModel(Model):
    ''' This class will represent a virtual world with different elements '''

    def __init__(self, N, width, height):
        self.width = width
        self.height = height
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(self.width, self.height, True)

        # Create a list of lists to store attribute of each cell (house, trail, road,...)
        # Further, this will be also used for agents/people's initial position and to direct in this map
        # self.cell_attribute = []
        self.background_cells = []

        # for x in range(self.width):
        #     # a number of list corresponding with a number of x cells (column)
        #     self.cell_attribute.append(list())
        # for inside_list in self.cell_attribute:
        #     for y in range(self.height):
        #         # a number of list corresponding with a number of y cells (row) for each column
        #         inside_list.append(list())

        # Create agent for cell and set its attribute
        count = 0   # for unique_id
        for x in range(self.width):
            for y in range(self.height):

                # Create cell agent
                cell_object = CellAgent(count, self)
                # Place this agent to the correct location of the model's grid
                self.grid.place_agent(cell_object, (x, y))
                cell_object.init_position = (x, y)
                # Set attribute for each cell
                self.set_attribute_cell(cell_object, x, y)

                # Set corresponding position in the attribute list to this type
                # self.cell_attribute[x][y] = cell_object.type
                self.background_cells.append(cell_object)

                count += 1

        # Find all road cells' position as possible runner's initial position
        self.roads = [
            cell.pos for cell in self.background_cells if cell.type == 'road']
        # Create runner agents
        for i in range(N):
            runner = RunnerAgent(i, self)
            # store the inital position as attribte
            runner.init_position = self.random.choice(self.roads)


<< << << < Updated upstream
            print('Initial position: ', runner.init_position)
== == == =
            # runner.init_position = (46, 21)
            # print('Initial position: ', runner.init_position)
>>>>>> > Stashed changes
            self.grid.place_agent(runner, runner.init_position)
            self.schedule.add(runner)

        # Attribute running for visualization
        self.running = True

    def step(self):
        ''' Activate the step for all runner agents at once '''
        self.schedule.step()

<<<<<<< Updated upstream
=======
        # stop once all agents finish running
        for agent in self.agent_objects:
            if agent.state == 'rest':
                self.num_agents_complete_running += 1
        if self.num_agents_complete_running == self.num_agents:
            self.running = False
            print('ALL AGENTS COMPLETED THEIR RUNNING')

            # HEAT MAP

            fig, ax = plt.subplots()
            sns.set_theme()

            xlabels = [i for i in range(self.width)]

            ax = sns.heatmap(self.heatmap_data, xticklabels=10, yticklabels=10)

            plt.tight_layout()
            plt.show()


        else:
            self.num_agents_complete_running = 0

>>>>>>> Stashed changes
    def set_attribute_cell(self, cell_object, x, y):
        # Attribute 'HOUSE' for cells
        if y >= 5 and y <= 7 and x >= 35 and x <= 37:
            cell_object.type = 'house'
        elif y >= 8 and y <= 10 and ((x >= 15 and x <= 17) or (x >= 20 and x <= 22) or (x >= 25 and x <= 27)):
            cell_object.type = 'house'
        elif y >= 14 and y <= 16 and ((x >= 15 and x <= 17) or (x >= 20 and x <= 22) or (x >= 25 and x <= 27)):
            cell_object.type = 'house'
        elif y >= 9 and y <= 11 and x >= 40 and x <= 42:
            cell_object.type = 'house'
        elif y >= 17 and y <= 19 and x >= 31 and x <= 33:
            cell_object.type = 'house'

        elif y >= 9 and y <= 11 and x >= 40 and x <= 42:
            cell_object.type = 'house'

        elif y >= 26 and y <= 28 and ((x >= 6 and x <= 8) or (x >= 13 and x <= 18)):
            cell_object.type = 'house'
        elif ((x >= 37 and x <= 39) or (x >= 42 and x <= 44)) and ((y >= 16 and y <= 18) or (y >= 25 and y <= 27) or (y >= 29 and y <= 31) or (y >= 33 and y <= 35) or (y >= 37 and y <= 39) or (y >= 41 and y <= 43)):
            cell_object.type = 'house'

        # ROAD
        elif x == 3 and (y >= 6 and y <= 32):
            cell_object.type = 'road'
        elif x == 7 and y <= 6:
            cell_object.type = 'road'
        elif x == 11 and (y >= 20 and y <= 30):
            cell_object.type = 'road'
        elif x == 12 and (y >= 6 and y <= 18):
            cell_object.type = 'road'
        elif x == 20 and (y >= 18 and y <= 30):
            cell_object.type = 'road'
        elif x == 29 and (y >= 21 and y <= 26):
            cell_object.type = 'road'
        elif x == 31 and y <= 12:
            cell_object.type = 'road'
        elif x == 35 and ((y >= 12 and y <= 13) or (y >= 26)):
            cell_object.type = 'road'
        elif x == 46 and (y >= 3 and y <= 45):
            cell_object.type = 'road'

        elif y == 3 and (x >= 31 and x <= 46):
            cell_object.type = 'road'
        elif y == 6 and (x >= 3 and x <= 31):
            cell_object.type = 'road'
        elif y == 12 and (x >= 3 and x <= 35):
            cell_object.type = 'road'
        elif y == 13 and (x >= 35 and x <= 46):
            cell_object.type = 'road'
        elif y == 18 and (x >= 12 and x <= 20):
            cell_object.type = 'road'
        elif y == 20 and (x >= 3 and x <= 20):
            cell_object.type = 'road'
        elif y == 21 and (x >= 29 and x <= 46):
            cell_object.type = 'road'
        elif y == 24 and (x >= 11 and x <= 20):
            cell_object.type = 'road'
        elif y == 26 and (x >= 20 and x <= 35):
            cell_object.type = 'road'
        elif y == 30 and (x >= 11 and x <= 20):
            cell_object.type = 'road'
        elif y == 40 and (x >= 30 and x <= 35):
            cell_object.type = 'road'
        elif y == 45 and (x >= 35 and x <= 46):
            cell_object.type = 'road'

        # TRAIL
        elif x == 3 and (y >= 33 and y <= 38):
            cell_object.type = 'trail'
        elif x == 7 and (y >= 38 and y <= 46):
            cell_object.type = 'trail'
        elif x == 12 and (y >= 35 and y <= 38):
            cell_object.type = 'trail'
        elif x == 16 and (y >= 42 and y <= 46):
            cell_object.type = 'trail'
        elif x == 20 and (y >= 35 and y <= 40):
            cell_object.type = 'trail'
        elif x == 25 and (y >= 40 and y <= 46):
            cell_object.type = 'trail'

        elif y == 35 and (x >= 12 and x <= 20):
            cell_object.type = 'trail'
        elif y == 38 and (x >= 3 and x <= 12):
            cell_object.type = 'trail'
        elif y == 40 and (x >= 20 and x <= 29):
            cell_object.type = 'trail'
        elif y == 42 and (x >= 7 and x <= 16):
            cell_object.type = 'trail'
        elif y == 46 and (x >= 7 and x <= 25):
            cell_object.type = 'trail'

        # FOREST
        elif x <= 29 and y >= 33:
            cell_object.type = 'forest'

        # GRASS
        else:
            cell_object.type = 'grass'

    # Find all road cells and return a list of multiple tuple positions of roads
    def find_road_cells(self, list_cells, width, height):
        position_roads = []
        for x in range(width):
            for y in range(height):
                if list_cells[x][y] == 'road':
                    position_roads.append((x, y))
        return position_roads


# world = VirtualWorldModel(51, 51)
# # # # # print(len(world.cell_attribute[49]))
# print(world.cell_attribute)
