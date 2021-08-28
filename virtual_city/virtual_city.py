from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from runner import RunnerAgent
import pandas as pd
import numpy as np
import seaborn as sns
import osmnx as ox
from matplotlib import pyplot as plt
import math


class CellAgent(Agent):
    ''' This class will represent cells in the grid world
        Purpose: Create visualization for the map
        Also, cells will stay with their same attribute, and color at the same location forever '''

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)


class VirtualCityModel(Model):
    ''' This class will represent a virtual neighborhood with different roads and runners roam around '''

    def __init__(self, N, width, height):
        # GRPAH INFORMATION
        self.graph = ox.graph_from_place(
            'Brentwood - Darlington, Portland, Oregon, USA', network_type='all')

        self.graph_edges = pd.read_csv(
            'Edges_data_from_network.csv', index_col=['u', 'v', 'key'])
        self.graph_nodes = pd.read_csv(
            'Nodes_data_from_network.csv', index_col='osmid')

        self.num_agents = N
        self.num_run_in_a_week = 4
        self.width = width
        self.height = height
        self.heatmap_data = np.zeros((self.height, self.width))
        self.schedule = RandomActivation(self)
        self.num_agents_complete_running = 0
        self.running = True
        self.grid = MultiGrid(self.width, self.height, True)

        self.possible_starting_cells = []   # [cell1, cell2, ...]

        self.cells_have_nodes = []  # [(cell_coord1), (cell_coord2), ...]
        self.cells_have_edges = []  # [(cell_coord1), (cell_coord2), ...]

        # [(cell_coord1), (cell_coord2), ...]
        self.cells_have_traffic_signals = []

        # {(cell_coord1): [osmid1,osmid2,..], (cell_coord2): [osmid1,osmid2,..]}
        self.nodes_of_cell = {}

        # {osmid1: (cell_coord), osmid2: (cell_coord),}
        self.cell_of_node = {}

        # {osmid1: [osmid1, osmid2], osmid2: []}.
        self.node_connections = {}

        # {(osmid1, osmid2, key): [cell1, cell2,..], }
        self.cells_of_edge = {}

        # {(osmid1, osmid2, key): num_of_using, (osmid3, osmid4, key): num_of_using, ...}
        self.memory_edge_using = {}

        self.primary = []
        self.secondary = []
        self.residential = []
        self.tertiary = []
        self.service = []
        self.footway = []
        self.path = []

        # all nodes osmid on footway road
        self.footway_all_nodes = []
        # all nodes coord on footway road
        self.footway_all_cells = []
        # nodes osmid on the road that runners could use to access at first
        self.footway_nodes_access = []
        self.footway_nodes_set1 = []    # park 1
        self.footway_nodes_set2 = []    # park 2

        # Append osmid of nodes to dictionaries
        for index in self.graph_nodes.index:
            self.cell_of_node[index] = None
            self.node_connections[index] = []

        count = 0   # for unique_id
        self.x_base = -122.6160279 - 0.000187
        self.y_base = 45.4614378 - 0.000187
        self.cell_gap = 0.000187

        # CREATE AGENTS FOR CELLS AND SET THEIR ATTRIBUTES
        # NODES
        self._set_nodes()

        # EDGES
        self._set_edges()

        # FOOTWAY LIST - PARK
        self._set_footway_list()

        # CREATE AGENTS FOR ALL NODE/EDGE CELLS (FOR VISUALIZATION)
        self._create_agent_for_node_and_edge()

        # CALENDAR - TIME
        self.calendar = ['MONDAY', 'TUESDAY', 'WEDNESDAY',
                         'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
        self.calendar_index = 0
        self.current_day = self.calendar[self.calendar_index]

        # LIST OF ALL RUNNER AGENTS
        self.agent_objects = []

        # CREATE AGENTS FOR RUNNERS
        for i in range(self.num_agents):
            runner = RunnerAgent(i, self)
            # store the inital position as an attribte
            runner.init_position = self.random.choice(
                self.possible_starting_cells)
            self.grid.place_agent(runner, runner.init_position)
            self.schedule.add(runner)
            self.agent_objects.append(runner)

            runner.get_initial_road_info()

            # update heatmap data
            x, y = runner.init_position
            self.heatmap_data[y][x] += 1

        self._set_personal_attribute_runner()
        self._set_up_day_to_run()
        for agent in self.agent_objects:
            agent.reset_possibility_rate()
            if self.current_day in agent.day_to_run:
                agent.get_ready()

        # DATACOLLECTOR
        self.datacollector = DataCollector(
            {'Going home (Pref 4)': 'agents_going_home', 'Agents got home': 'agents_got_home', 'Preference 1': 'agents_with_pref1', 'Preference 2': 'agents_with_pref2', 'Preference 3': 'agents_with_pref4'}, {})

    def _set_up_day_to_run(self):
        for agent in self.agent_objects:
            self.calendar_copy = self.calendar[:]
            for i in range(self.num_run_in_a_week):
                day = self.random.choice(self.calendar_copy)
                agent.day_to_run.append(day)
                self.calendar_copy.remove(day)

    def step(self):
        ''' Activate the step for all runner agents at once '''

        # ACTIVATE THE AGENTS
        self.schedule.step()

        # UPDATE DATA COLLECTOR
        self.agents_going_home = len(
            [agent for agent in self.agent_objects if agent.want_to_go_home and agent.state != 'rest'])
        self.agents_got_home = len(
            [agent for agent in self.agent_objects if agent.state == 'rest'])
        self.agents_with_pref1 = len(
            [agent for agent in self.agent_objects if agent.preference == 'preference1'])
        self.agents_with_pref2 = len(
            [agent for agent in self.agent_objects if agent.preference == 'preference2'])
        self.agents_with_pref4 = len(
            [agent for agent in self.agent_objects if agent.preference == 'preference3'])

        self.datacollector.collect(self)

        # STOP ALL AGENTS AND SHOW HEATMAP ONCE ALL AGENTS COMPLETE THEIR RUNS AND CHANGE TO NEW DAY
        for agent in self.agent_objects:
            if agent.state == 'rest':
                self.num_agents_complete_running += 1
        if self.num_agents_complete_running == self.num_agents:
            print('ALL AGENTS COMPLETED THEIR RUNNING BY THE END OF',
                  self.current_day)

            # HEAT MAP
            if self.calendar.index(self.current_day) == (len(self.calendar) - 1):
                print('END OF THE WEEK')
                fig, ax = plt.subplots(figsize=(10, 4))
                sns.set_theme()

                ax = sns.heatmap(self.heatmap_data,
                                 xticklabels=10, yticklabels=10)
                plt.gca().invert_yaxis()
                plt.tight_layout()
                plt.show()
                self.running = False

            print('Preapring for the next day...')
            if self.calendar_index != (len(self.calendar) - 1):
                self.next_day()
                print('\nTODAY: ', self.current_day)

        self.num_agents_complete_running = 0

    def next_day(self):

        # update new day
        self.calendar_index += 1
        self.current_day = self.calendar[self.calendar_index]
        for agent in self.agent_objects:
            x, y = agent.init_position
            # heatmap
            self.heatmap_data[y][x] += 1
            agent.reset_runner_info()
            agent.get_initial_road_info()
            agent.reset_possibility_rate()

            if self.current_day in agent.day_to_run:
                agent.get_ready()
                agent.state = '_continue_forward'

    def _memorize_roads(self, pos, u, v, k):
        ''' Append to the list of road and memorize it as a connection between 2 intersection so agents can access '''

        # append to list of road
        if pos not in self.cells_have_nodes:
            self.cells_have_edges.append(pos)

        # append the road cells if the type road is different from these
        if self.road_type != 'service' and self.road_type != 'path' and self.road_type != 'footway':
            if pos not in self.possible_starting_cells and pos not in self.cells_have_nodes:
                self.possible_starting_cells.append(pos)

        # List all types of roads
        if self.road_type == 'secondary':
            self.secondary.append(pos)
        elif self.road_type == 'primary':
            self.primary.append(pos)
        elif self.road_type == 'residential':
            self.residential.append(pos)
        elif self.road_type == 'tertiary':
            self.tertiary.append(pos)
        elif self.road_type == 'service':
            self.service.append(pos)
        elif self.road_type == 'footway':
            self.footway.append(pos)
        elif self.road_type == 'path':
            self.path.append(pos)

        # connection between 2 intersections
        if not self.switch_order:
            if k == 0:
                self.cells_of_edge[(u, v, k)].append(pos)
            # Don't have to memorize the parking lot/way
            elif k == 1 and self.graph_edges.loc[(u, v, k)]['highway'] != 'service':
                pass

        else:  # the order has been switched
            if k == 0:
                self.cells_of_edge[(u, v, k)].insert(0, pos)
            # Don't have to memorize the parking lot/way
            elif k == 1 and self.graph_edges.loc[(u, v, k)]['highway'] != 'service':
                pass

    def _set_footway_list(self):

        # APPEND TO THE LIST OF ALL FOOTWAY NODES AND FOOTWAY CELLS
        for index in list(self.graph_edges.index):
            if self.graph_edges.loc[index]['highway'] == 'footway':
                u, v, k = index
                if u not in self.footway_all_nodes:
                    pos_x, pos_y = self.cell_of_node[u]
                    if pos_x > 50 and pos_x < 150:
                        self.footway_all_nodes.append(u)
                        self.footway_all_cells.append(self.cell_of_node[u])
                if v not in self.footway_all_nodes:
                    pos_x, pos_y = self.cell_of_node[v]
                    if pos_x > 50 and pos_x < 150:
                        self.footway_all_nodes.append(v)
                        self.footway_all_cells.append(self.cell_of_node[v])

        # APPEND TO FOOTWAY SET1 AND SET2 APPROPRIATELY
        for cell in self.footway_all_cells:
            current_index = self.footway_all_cells.index(cell)
            x, y = cell
            if y > 40:
                self.footway_nodes_set1.append(
                    self.footway_all_nodes[current_index])
            else:
                self.footway_nodes_set2.append(
                    self.footway_all_nodes[current_index])

        # APPEND TO NODE LIST FOR ACCESS
        for osmid in self.footway_all_nodes:
            appended = False
            for row in self.graph_edges.loc[osmid]['highway']:
                if row != 'footway' and appended == False:
                    self.footway_nodes_access.append(osmid)
                    appended = True

    def _set_personal_attribute_runner(self):
        # SET RUNNER'S PERSONAL ATTRIBUTE
        self.total_male = self.num_agents / 2
        self.total_female = self.total_male

        self.total_male_low = math.ceil(0.27 * self.total_male)
        self.total_male_moderate = math.ceil(0.23 * self.total_male)
        self.total_male_high = math.ceil(0.24 * self.total_male)
        self.total_male_very_high = math.ceil(self.total_male - self.total_male_low -
                                              self.total_male_moderate - self.total_male_high)

        self.total_female_low = math.ceil(0.42 * self.total_female)
        self.total_female_moderate = math.ceil(0.26 * self.total_female)
        self.total_female_high = math.ceil(0.17 * self.total_female)
        self.total_female_very_high = math.ceil(self.total_female - self.total_female_low -
                                                self.total_female_moderate - self.total_female_high)

        self.male_group = []
        self.female_group = []

        self.male_low = []
        self.male_moderate = []
        self.male_high = []
        self.male_very_high = []

        self.female_low = []
        self.female_moderate = []
        self.female_high = []
        self.female_very_high = []

        # SET GENDER
        number_of_male = 0
        for agent in self.agent_objects:
            if number_of_male < self.total_male:
                agent.gender = 'male'
                self.male_group.append(agent)
            else:
                agent.gender = 'female'
                self.female_group.append(agent)
            number_of_male += 1

        # SET FITNESS LEVEL AND WEEKLY DISTANCE GOAL
        # Male
        max_index_low = self.total_male_low
        for i in range(max_index_low):
            self.male_group[i].fitness_level = 'low'
            self.male_group[i].weekly_distance_goal = self.random.randrange(
                5000, 20000)
            self.male_low.append(self.male_group[i])
        max_index_moderate = max_index_low + self.total_male_moderate
        for i in range(max_index_low, max_index_moderate):
            self.male_group[i].fitness_level = 'moderate'
            self.male_group[i].weekly_distance_goal = self.random.randrange(
                21000, 30000)
            self.male_moderate.append(self.male_group[i])
        max_index_high = max_index_moderate + self.total_male_high
        for i in range(max_index_moderate, max_index_high):
            self.male_group[i].fitness_level = 'high'
            self.male_group[i].weekly_distance_goal = self.random.randrange(
                31000, 40000)
            self.male_high.append(self.male_group[i])
        max_index_very_high = max_index_high + self.total_male_very_high
        for i in range(max_index_high, max_index_very_high):
            self.male_group[i].fitness_level = 'very_high'
            self.male_group[i].weekly_distance_goal = self.random.randrange(
                41000, 50000)
            self.male_very_high.append(self.male_group[i])

        # Female
        max_index_low = self.total_female_low
        for i in range(max_index_low):
            self.female_group[i].fitness_level = 'low'
            self.female_group[i].weekly_distance_goal = self.random.randrange(
                5000, 20000)
            self.female_low.append(self.female_group[i])
        max_index_moderate = max_index_low + self.total_female_moderate
        for i in range(max_index_low, max_index_moderate):
            self.female_group[i].fitness_level = 'moderate'
            self.female_group[i].weekly_distance_goal = self.random.randrange(
                21000, 30000)
            self.female_moderate.append(self.female_group[i])
        max_index_high = max_index_moderate + self.total_female_high
        for i in range(max_index_moderate, max_index_high):
            self.female_group[i].fitness_level = 'high'
            self.female_group[i].weekly_distance_goal = self.random.randrange(
                31000, 40000)
            self.female_high.append(self.female_group[i])
        max_index_very_high = max_index_high + self.total_female_very_high
        for i in range(max_index_high, max_index_very_high):
            self.female_group[i].fitness_level = 'very_high'
            self.female_group[i].weekly_distance_goal = self.random.randrange(
                41000, 50000)
            self.female_very_high.append(self.female_group[i])

        # DISTANCE GOAL
        for agent in self.agent_objects:
            agent.distance_goal = agent.weekly_distance_goal / \
                len(self.calendar)
            # (for quick testing)
            # agent.distance_goal = agent.weekly_distance_goal / 400

    def _set_nodes(self):
        for index in self.graph_nodes.index.tolist():
            # get the real coordinates of nodes
            this_node_x = self.graph_nodes.loc[index]['x']
            this_node_y = self.graph_nodes.loc[index]['y']

            # loop through list of x and y to get correct cell's coord for this node
            for x_cell_coord in range(self.width):
                start_cell = self.x_base + (x_cell_coord * self.cell_gap)
                end_cell = start_cell + self.cell_gap
                if start_cell <= this_node_x and this_node_x < end_cell:
                    x = x_cell_coord
                    break
            for y_cell_coord in range(self.height):
                start_cell = self.y_base + (y_cell_coord * self.cell_gap)
                end_cell = start_cell + self.cell_gap
                if start_cell <= this_node_y and this_node_y < end_cell:
                    y = y_cell_coord
                    break

            # adding the coord of this cell to a list of nodes
            if (x, y) not in self.cells_have_nodes:
                self.cells_have_nodes.append((x, y))
            # store this cell coord for the node
            self.cell_of_node[index] = (x, y)
            # store this nodes to this current cell
            if (x, y) not in self.nodes_of_cell:
                self.nodes_of_cell[(x, y)] = []
            self.nodes_of_cell[(x, y)].append(
                index)  # append the osmid of this node to the cell

            # adding this coord of this cell to list of traffic light
            if self.graph_nodes.loc[index]['highway'] == 'traffic_signals' and (x, y) not in self.cells_have_traffic_signals:
                self.cells_have_traffic_signals.append((x, y))

    def _set_edges(self):
        # ROAD FOR THE EDGES
        for index, row in self.graph_edges.iterrows():

            u, v, k = index

            cell1 = self.cell_of_node[u]
            cell2 = self.cell_of_node[v]

            self.node_connections[u].append(v)
            # Eliminate all alternative roads of two points and that road is a paking way, way leading to building
            if k == 1 and self.graph_edges.loc[index]['highway'] == 'service':
                pass
            else:
                self.cells_of_edge[index] = []

            # Memory all edge for level of using
            self.memory_edge_using[index] = 0

            # Memorize the type of road to put into corresponding list for creating
            self.road_type = self.graph_edges.loc[index]['highway']

            # Get grid coordinate
            self.switch_order = False
            x1, y1 = cell1
            x2, y2 = cell2

            # Find the gap in x and gap in y coord.
            gap_in_x = abs(x2 - x1)
            gap_in_y = abs(y2 - y1)

            # STRAIGHT VERTICAL ROAD
            if gap_in_x == 0 and gap_in_y != 0:
                # Assume that y2 of cell2 > y1 of cell1
                # but if opposite, then switch the order
                if y1 > y2:  # so y2 is always greater than y1
                    x1, y1 = cell2
                    x2, y2 = cell1
                    self.switch_order = True

                real_gap_in_y = y2 - y1 - 1
                y = y1 + 1
                x = x1
                num_cells_on_top = 1
                while num_cells_on_top <= real_gap_in_y:
                    # append to list of road, and the road for corresponding connection
                    self._memorize_roads((x, y), u, v, k)
                    y += 1
                    num_cells_on_top += 1

            # STRAIGHT HORIZONTAL ROAD
            elif gap_in_y == 0 and gap_in_x != 0:

                if x1 > x2:
                    x1, y1 = cell2
                    x2, y2 = cell1
                    self.switch_order = True

                real_gap_in_x = x2 - x1 - 1
                x = x1 + 1
                y = y1
                num_cells_on_right = 1
                while num_cells_on_right <= real_gap_in_x:
                    self._memorize_roads((x, y), u, v, k)
                    x += 1
                    num_cells_on_right += 1

            # PERFECT DIAGONAL ROAD
            elif gap_in_y != 0 and gap_in_y != 1 and abs(gap_in_y) == abs(gap_in_x):

                # Assume that y2 of cell2 > y1 of cell1
                # but if opposite, then switch the order
                if y1 > y2:
                    x1, y1 = cell2
                    x2, y2 = cell1  # so y2 is always greater than y1
                    self.switch_order = True

                # check x1 is on left or right compare to x2
                side = None
                next_x = 0
                if x1 - x2 > 0:
                    next_x = -1  # x1 on the right, so next x must -1
                else:
                    next_x = 1  # x1 on the right, so next x must +1

                real_gap_in_y = y2 - y1 - 1

                x = x1 + next_x
                y = y1 + 1
                num_diag_cells = 1
                while num_diag_cells <= real_gap_in_y:
                    self._memorize_roads((x, y), u, v, k)
                    x = x + next_x
                    y = y + 1
                    num_diag_cells += 1

            # CREATE NOT A PERFECT DIAGONAL ROAD
            # gap in y is greater than gap in x
            elif abs(gap_in_y) > abs(gap_in_x):

                # Assume that y2 of cell2 > y1 of cell1
                # but if opposite, then switch the order
                if y1 > y2:
                    x1, y1 = cell2
                    x2, y2 = cell1
                    self.switch_order = True

                real_gap_in_y = y2 - y1 - 1
                real_gap_in_x = abs(x2 - x1) - 1
                gap_bw_y_and_x = real_gap_in_y - real_gap_in_x

                # create cells above cell1
                num_cells_on_top_cell1 = 1
                y = y1 + 1
                while num_cells_on_top_cell1 <= gap_bw_y_and_x:
                    # append to the list of cells for edges to create late
                    x = x1
                    self._memorize_roads((x, y), u, v, k)

                    y += 1
                    num_cells_on_top_cell1 += 1

                # x1 on the right --> next x must be decreased by 1
                if x1 - x2 > 0:
                    next_x = -1
                # x1 on the left --> next x must be increased by 1
                else:
                    next_x = 1

                # create diagonal cells if necessary
                num_diagonal_cells = 1
                while num_diagonal_cells <= real_gap_in_x:
                    x = x + next_x

                    self._memorize_roads((x, y), u, v, k)
                    y += 1
                    num_diagonal_cells += 1

            # gap in x is greater than gap in y
            elif gap_in_y < abs(gap_in_x):

                if x1 > x2:
                    x, y = x1, y1
                    x1, y1 = x2, y2
                    x2, y2 = x, y
                    self.switch_order = True

                real_gap_in_y = abs(y2 - y1) - 1
                real_gap_in_x = x2 - x1 - 1
                gap_bw_y_and_x = real_gap_in_x - real_gap_in_y

                # create cells on right of cell1
                num_cells_on_right_cell1 = 1
                x = x1 + 1
                while num_cells_on_right_cell1 <= gap_bw_y_and_x:
                    # append to the list of cells for edges to create late
                    y = y1
                    self._memorize_roads((x, y), u, v, k)

                    x += 1
                    num_cells_on_right_cell1 += 1

                # check y1 is up or down compare to y2
                # y1 on the top --> next y must be decreased by 1
                if y1 - y2 > 0:
                    next_y = -1
                # y1 on the down --> next y must be increased by 1
                else:
                    next_y = 1

                # create diagonal cells if necessary
                num_diagonal_cells = 1
                while num_diagonal_cells <= real_gap_in_y:
                    y = y + next_y

                    self._memorize_roads((x, y), u, v, k)
                    x += 1
                    num_diagonal_cells += 1

    def _create_agent_for_node_and_edge(self):
        count = 0   # for unique_id
        for x in range(self.width):
            for y in range(self.height):

                # Create cell agent
                cell_object = CellAgent(count, self)
                # Place this agent to the correct location of the model's grid
                self.grid.place_agent(cell_object, (x, y))
                cell_object.init_position = (x, y)

                # Set attribute for each cell
                cell_object.type = 'grass'

                if (x, y) in self.cells_have_traffic_signals:
                    cell_object.type = 'traffic_signals'
                elif (x, y) in self.cells_have_nodes:
                    cell_object.type = 'intersection'
                elif (x, y) in self.secondary:
                    cell_object.type = 'secondary'
                elif (x, y) in self.primary:
                    cell_object.type = 'primary'
                elif (x, y) in self.residential:
                    cell_object.type = 'residential'
                elif (x, y) in self.tertiary:
                    cell_object.type = 'tertiary'
                elif (x, y) in self.service:
                    cell_object.type = 'service'
                elif (x, y) in self.footway:
                    cell_object.type = 'footway'
                elif (x, y) in self.path:
                    cell_object.type = 'path'
                elif (x, y) in self.cells_have_edges:
                    cell_object.type = 'road'
