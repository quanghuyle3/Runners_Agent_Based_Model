from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from runner import RunnerAgent
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns


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
        self.num_agents = N
        self.schedule = RandomActivation(self)
        self.heatmap_data = np.zeros((self.height, self.width))
        self.grid = MultiGrid(self.width, self.height, True)

        self.background_cells = []

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

                # Append to the list containing all background cells
                self.background_cells.append(cell_object)

                count += 1

        # Find all road cells' position as possible runner's initial position
        self.roads = [
            cell.pos for cell in self.background_cells if cell.type == 'road']
        # Create runner agents
        self.agent_objects = []
        for i in range(self.num_agents):
            runner = RunnerAgent(i, self)
            # store the inital position as attribte
            runner.init_position = self.random.choice(self.roads)

            print('Initial position: ', runner.init_position)

            self.grid.place_agent(runner, runner.init_position)
            self.schedule.add(runner)
            self.agent_objects.append(runner)

            # update heatmap data
            x, y = runner.init_position
            self.heatmap_data[self.height - 1 - y][x] += 1

        # Attribute running for visualization
        self.running = True

        # Trail entrance point
        self.trail_entrance_point = [(3, 32), (30, 40)]

        self.num_agents_complete_running = 0

    def step(self):
        ''' Activate the step for all runner agents at once '''
        self.schedule.step()

        # stop once all agents finish running
        for agent in self.agent_objects:
            if agent.state == 'rest':
                self.num_agents_complete_running += 1
        if self.num_agents_complete_running == self.num_agents:
            self.running = False
            print('ALL AGENTS COMPLETED THEIR RUNS')

            # HEAT MAP
            fig, ax = plt.subplots()
            sns.set_theme()

            ax = sns.heatmap(self.heatmap_data, xticklabels=10, yticklabels=10)

            plt.tight_layout()
            plt.show()

        else:
            self.num_agents_complete_running = 0

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
