from mesa import Agent, Model
from mesa.space import MultiGrid
import networkx as nx


class RunnerAgent(Agent):
    ''' This class will represent runners in this model '''

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.reset_runner_info()
        self.day_to_run = []

    def reset_runner_info(self):
        # Personal attributes
        self.type = 'runner'
        self.preference = None
        self.state = 'rest'
        self.distance_gone = 0
        self.estimate_distance_back_home = 0
        self.estimate_distance_back_home_previous = 0
        self.estimate_distance_cell_to_init_point = 0
        self.check_closer_or_farer = 0
        self.want_to_go_home = False
        self.begin_going_home = False

        # Possibility rate that runner choose an alternative road only once at intersection on the way home instead of following shortest path
        self.possibility_change_way_home = 0.2
        # Possibility rate that runner choose an alternative road only once at intersection on the way to park instead of following shostest path
        self.possibility_change_way_park = 0.1

        # NODE GONE MEMORY
        self.memory_node_osmid = []
        self.memory_node_coord = []
        # NODE DEAD END MEMORY
        self.memory_deadend_osmid = []
        self.memory_deadend_coord = []

        # ADDITION MEMORY ON THE WAY GO HOME
        self.memory_node_osmid_way_home = []
        self.memory_node_coord_way_home = []

        # EDGE/ROAD ATTRIBUTES
        self.init_road_name = None
        self.init_road_index = None
        self.init_road_type = None
        self.init_index = None          # choose one index from init road index
        self.current_road_name = None
        self.current_road_index = None
        self.current_road_type = None
        self.current_road_cells = None
        self.current_road_length = None
        self.amount_added = None

        # index of cell within the list cells of current edge
        self.current_cell_index_on_roadset = None
        self.num_cells_gone_on_road = None

        # END POINTS OF A STRAIGHT ROAD
        self.endpoint1 = None
        self.endpoint2 = None
        self.start_from_one_endpoint = False
        self.finish_at_one_endpoint = False
        # total length of this current straight road
        self.straight_road_length = 0

        # NODE ATTRIBUTES
        self.current_node_index = None
        self.current_node_position = None
        self.next_node_index = None  # osmid of next node
        self.next_node_position = None  # grid coord of next node/intersection.
        self.previous_node_index = None
        self.previous_node_position = None
        self.to_node = None  # 'u' or 'v'

        # CONSIDER NEXT NODE AT INTERSECTION
        self.possible_next_node_index = []
        self._set_consider_list_node()

        # type of roads around, not including previous road
        self.type_roads_around = []

        # ON THE PARK FLAG
        self.on_the_park = False
        self.target_node_coming_park = None
        self.current_set_node_on_park = None
        self.target_node_running_around_park = None

        self.start_on_road = False

        self.key = None

        # POSSIBILITY RATE
        # to make a turn at the traffic signals point
        self.pr_turn_at_traffic_signals = None
        # to go straight (get over) at the traffic signals point
        self.pr_go_straight_at_traffic_signals = None
        self.pr_turn_on_ter = None  # to make a turn on tertiary roads
        self.pr_turn_on_sec = None  # to make a turn on secondary roads
        self.pr_turn_on_pri = None  # to make a turn on primary roads
        self.pr_turn_on_res = None  # to make a turn on residential roads

        # to go to the park at first
        self.pr_go_to_park = None
        # to continue its running on the park when come across
        self.pr_continue_on_park = None
        # distance want to run on around park
        self.distance_run_around_park = None
        # the distance point that once reached, runner will go home or get out park and continue running
        self.distance_will_get_out_park = None
        # follow preference 1 when start on residential road
        self.pr_start_pref1_on_res = None
        # follow preference 2 when start on tertiary or secondary road
        self.pr_start_pref2_on_ter_sec = None

        # Preference while running
        self.preference = None

    def _set_consider_list_node(self):
        self.list_node_on_same_road_name = []
        self.list_node_on_same_road_type = []
        self.list_node_on_other_road_type = []

    def get_initial_road_info(self):

        # Flag start on road for calculating the distance
        self.start_on_road = True
        self.num_cells_gone_on_road = 0

        # Figure out what road the runner is standing now
        for key, value in self.model.cells_of_edge.items():
            if self.init_position in value:

                u, v, k = key

                # EDGE/ROAD
                # Get road info
                self.init_road_name = self.model.graph_edges.loc[key]['name']
                self.current_road_name = self.model.graph_edges.loc[key]['name']
                self.current_road_type = self.model.graph_edges.loc[key]['highway']
                self.current_road_length = self.model.graph_edges.loc[key]['length']

                # Find list of all cells in this current road
                self.current_road_cells = self.model.cells_of_edge[key]

                # store the tuple key of this initial road
                self.init_road_index = key
                self.current_road_index = key

                self.init_road_type = self.model.graph_edges.loc[key]['highway']

                # NODES
                # Choose one of these nodes as next destination
                self.next_node_index = self.random.choice([u, v])

                # Find the pos of next node
                self.next_node_position = self.model.cell_of_node[self.next_node_index]

                # Find current index of cell start, in the list of the current road cells
                self.current_cell_index_on_roadset = self.current_road_cells.index(
                    self.init_position)

                # Store cell behind as memory so runner could avoid at first
                if self.next_node_index != u:
                    self.memory_node_osmid.append(u)
                    self.memory_node_coord.append(self.model.cell_of_node[u])
                    self.memory_node_coord
                elif self.next_node_index != v:
                    self.memory_node_osmid.append(v)
                    self.memory_node_coord.append(self.model.cell_of_node[v])

                # check to see runner goes to u or v
                if self.next_node_index == u:
                    self.to_node = 'u'
                else:
                    self.to_node = 'v'
                break

    def reset_possibility_rate(self):

        # POSSIBILITY RATE AT AN INTERSECTION
        self.pr_turn_at_traffic_signals = 0.8
        self.pr_go_straight_at_traffic_signals = 0.2

        # POSSIBILITY RATE TO TURN
        if self.init_road_type == 'primary':
            self.pr_turn_on_pri = None
            self.pr_turn_on_sec = 0.5
            self.pr_turn_on_ter = 0.5
            self.pr_turn_on_res = 0.2
        elif self.init_road_type == 'tertiary' or self.init_road_type == 'secondary':
            self.pr_turn_on_pri = 0.4
            self.pr_turn_on_sec = 0.4
            self.pr_turn_on_ter = 0.4
            self.pr_turn_on_res = 0.1

        elif self.init_road_type == 'residential':
            if self.gender == 'male':
                self.pr_turn_on_pri = 0.2
                self.pr_turn_on_sec = 0.4
                self.pr_turn_on_ter = 0.4
                self.pr_turn_on_res = 0.3

            elif self.gender == 'female':
                self.pr_turn_on_pri = 0.2
                self.pr_turn_on_sec = 0.4
                self.pr_turn_on_ter = 0.4
                self.pr_turn_on_res = 0.3

        # POSSIBILITY TO GO TO PARK AT FIRST AND CONTINUE RUNNING ON THE PARK (when come across)
        # POSSIBILITY TO START WITH PREFERENCE 1 AT FIRST
        if self.gender == 'male':
            if self.fitness_level == 'low':
                self.pr_go_to_park = 0.4
                self.pr_start_pref1_on_res = 0.3
                self.pr_start_pref2_on_ter_sec = 0.9
            elif self.fitness_level == 'moderate':
                self.pr_go_to_park = 0.35
                self.pr_start_pref1_on_res = 0.4
                self.pr_start_pref2_on_ter_sec = 0.85
            elif self.fitness_level == 'high':
                self.pr_go_to_park = 0.2
                self.pr_start_pref1_on_res = 0.6
                self.pr_start_pref2_on_ter_sec = 0.8
            elif self.fitness_level == 'very_high':
                self.pr_go_to_park = 0.15
                self.pr_start_pref1_on_res = 0.7
                self.pr_start_pref2_on_ter_sec = 0.8
            self.pr_continue_on_park = 0.12

        if self.gender == 'female':
            if self.fitness_level == 'low':
                self.pr_go_to_park = 0.6
                self.pr_start_pref1_on_res = 0.1
                self.pr_start_pref2_on_ter_sec = 0.9
            elif self.fitness_level == 'moderate':
                self.pr_go_to_park = 0.45
                self.pr_start_pref1_on_res = 0.2
                self.pr_start_pref2_on_ter_sec = 0.85
            elif self.fitness_level == 'high':
                self.pr_go_to_park = 0.4
                self.pr_start_pref1_on_res = 0.3
                self.pr_start_pref2_on_ter_sec = 0.8
            elif self.fitness_level == 'very_high':
                self.pr_go_to_park = 0.3
                self.pr_start_pref1_on_res = 0.4
                self.pr_start_pref2_on_ter_sec = 0.8
            self.pr_continue_on_park = 0.2

        # distance run around park
        self.distance_run_around_park = None
        # the distance point to go home or get out park
        self.distance_will_get_out_park = None

    def _set_distance_run_around_park(self):
        # SET THE DISTANCE THAT RUNNERS WILL RUN BEFORE ASSIGNED preference 2 TO CONTINUE
        if self.fitness_level == 'low' or self.fitness_level == 'moderate':
            portion = self.random.randrange(60, 90)  # 60% - 90%
        elif self.fitness_level == 'high' or self.fitness_level == 'very_high':
            portion = self.random.randrange(30, 60)  # 30% - 60%

        self.distance_run_around_park = (
            portion / 100) * (self.distance_goal - self.distance_gone - self.estimate_distance_back_home)
        # reach this distance, then go home or get out of park
        self.distance_will_get_out_park = self.distance_run_around_park + self.distance_gone

    def get_ready(self):

        self.state = '_continue_forward'

        # CHECK IF WANT TO GO TO PARK AT FIRST
        # find the length of shortest path
        length_shortest_path = None
        for index in self.model.footway_nodes_access:
            length = nx.shortest_path_length(
                self.model.graph, self.next_node_index, index, weight='length')

            if length_shortest_path == None or length < length_shortest_path:
                length_shortest_path = length

        # if len of shortest path < 480m and fall within rate
        if length_shortest_path < 480 and self.random.random() < self.pr_go_to_park:
            self.preference = 'preference3'

        if self.preference == None:
            if self.current_road_type == 'residential':
                # check if want to start with pref 1
                if self.random.random() < self.pr_start_pref1_on_res:
                    self.preference = 'preference1'
                # otherwise, assign pref 2
                else:
                    self.preference = 'preference2'

            elif self.current_road_type == 'tertiary' or self.current_road_type == 'secondary':
                # check if want to start with pref 2
                if self.random.random() < self.pr_start_pref2_on_ter_sec:
                    self.preference = 'preference2'
                else:
                    self.preference = 'preference1'
            elif self.current_road_type == 'primary':
                self.preference = 'preference2'
            else:
                # for a few agents in special area (footway but not footway in real life)
                self.preference = 'preference1'

    def step(self):

        # Reaasigne preference 2 for preference 1 if runners are on one-way road (avoid error)
        if self.preference == 'preference2' and self.model.graph_edges.loc[self.current_road_index]['oneway'] == True:
            self.preference = 'preference1'

        # FOLLOW STATE MACHINE BY ITS OWN TYPE AND PREFERENCE
        if self.want_to_go_home and self.pos == self.init_position:
            self.state = 'rest'
        elif not self.want_to_go_home:
            if self.preference == 'preference1':
                self.preference1()
            elif self.preference == 'preference2':
                self.preference2()
            elif self.preference == 'preference3':
                self.preference3()
        elif self.want_to_go_home:
            self.preference4()

    # RUNNING ON ROADS AS STRAIGHT AS POSSIBLE, AND AVOID REPEATING ROUTES

    def preference1(self):
        if self.state == '_continue_forward':
            self.continue_forward()
        elif self.state == '_intersection':
            self.intersection1()

    # RUNNING ON A STRAIGHT ROAD BACK AND FORTH
    def preference2(self):
        if self.state == '_continue_forward':
            self.continue_forward()
        elif self.state == '_intersection':
            self.intersection2()

    # GET TO THE PARK AS SOON AS IT CAN AND RUNNING A WHILE UNTIL WANT TO GO HOME OR CHANGE TO OTHER STATE AND KEEP RUNNING
    def preference3(self):
        if self.state == '_continue_forward':
            self.continue_forward()
        elif self.state == '_intersection':
            self.intersection3()

    # GET BACK TO THE INITIAL POSSITION AS SOON AS IT CAN BY FOLLOWING THE SHORTEST PATH

    def preference4(self):
        if self.state == '_continue_forward':
            self.continue_forward()
        elif self.state == '_intersection':
            self.intersection4()

    def continue_forward(self):
        # About to get to the destination if at the an endpoint (before node) of road
        if self.to_node == 'u' and self.current_cell_index_on_roadset == 0:
            # update previous node before current node
            self.previous_node_index = self.current_node_index
            self.previous_node_position = self.current_node_position
            self.current_node_index = self.next_node_index
            self.current_node_position = self.next_node_position
            # get to u position
            self.next_position = self.next_node_position

            # update distance
            self._adding_distance_goal()
            # change state
            self.state = '_intersection'

        # About to get to the destination if at the an endpoint (after node) of road
        elif self.to_node == 'v' and self.current_cell_index_on_roadset == len(self.current_road_cells) - 1:
            # update previous node before current node
            self.previous_node_index = self.current_node_index
            self.previous_node_position = self.current_node_position
            self.current_node_index = self.next_node_index
            self.current_node_position = self.next_node_position
            # get to v position
            self.next_position = self.next_node_position
            # update distance
            self._adding_distance_goal()
            # change state
            self.state = '_intersection'

        # Move to next cell if still on road
        elif self.to_node == 'u':
            self.current_cell_index_on_roadset = self.current_cell_index_on_roadset - 1
            self.next_position = self.current_road_cells[self.current_cell_index_on_roadset]
        elif self.to_node == 'v':
            self.current_cell_index_on_roadset = self.current_cell_index_on_roadset + 1
            self.next_position = self.current_road_cells[self.current_cell_index_on_roadset]

        # Make a move
        self._move_agent_update_attributes()

    def switch_previous_and_current_node_index(self):
        # update previous node before current node
        self.previous_node_index = self.current_node_index
        self.previous_node_position = self.previous_node_position
        self.current_node_index = self.next_node_index
        self.current_node_position = self.next_node_position
        pass

    def intersection1(self):
        # STORE INTERSECTION FOR MEMORY
        # intersection memory
        self.memory_node_osmid.append(self.current_node_index)
        self.memory_node_coord.append(self.current_node_position)

        # dead end memory
        if len(self.model.graph_edges.loc[self.current_node_index]['osmid']) == 1 and self.current_node_index not in self.init_road_index:
            self.memory_deadend_osmid.append(self.current_node_index)
            self.memory_deadend_coord.append(self.current_node_position)

        # CHOOSE NEXT NODE IN THE SAME ROAD OR SAME TYPE
        # find all possible nodes around
        self.possible_next_node_index = self.model.node_connections[self.current_node_index]

        # ignore all known dead ends
        self.possible_next_node_index_copy = [
            index for index in self.possible_next_node_index if index not in self.memory_deadend_osmid]

        # ignore previous road
        self.possible_next_node_index_copy1 = [
            index for index in self.possible_next_node_index if index != self.previous_node_index]

        # ignore all roads have been gone
        self.possible_next_node_index_copy2 = [
            index for index in self.possible_next_node_index if index not in self.memory_node_osmid]

        # if at dead end for first time --> u turn (intersection of 1)
        if len(self.possible_next_node_index_copy1) == 0:
            self.next_node_index = self.possible_next_node_index_copy[0]

        # encounter traffic signals
        elif self.model.graph_nodes.loc[self.current_node_index]['highway'] == 'traffic_signals':
            self.list_straight_road = [index for index in self.possible_next_node_index_copy1[:] if self.model.graph_edges.loc[(
                self.current_node_index, index, 0)]['name'] == self.current_road_name]
            # make a turn if don't have straight road or fall within the possibility rate of turning
            if len(self.list_straight_road) == 0 or self.random.random() < self.pr_turn_at_traffic_signals:
                self.next_node_index = self.random.choice([index for index in self.possible_next_node_index_copy1[:] if self.model.graph_edges.loc[(
                    self.current_node_index, index, 0)]['name'] != self.current_road_name])

            # or go straight
            else:
                self.next_node_index = self.list_straight_road[0]

        # choose a random road if all roads around have been gone (intersection of 3-4)
        elif len(self.possible_next_node_index_copy2) == 0:
            self.next_node_index = self.random.choice(
                self.possible_next_node_index_copy1)

        # otherwise, take the road have the same name
        # no same name, choose same type of road
        # no same type of road, prefer primary, secondary, tertiary, or residential
        else:

            self._set_consider_list_node()
            for index in self.possible_next_node_index_copy2:
                self.current_road_index = (self.current_node_index, index, 0)
                # list node on current road name
                if self.model.graph_edges.loc[self.current_road_index]['name'] == self.current_road_name:
                    self.list_node_on_same_road_name.append(index)
                # list node on current road type
                elif self.model.graph_edges.loc[self.current_road_index]['highway'] == self.current_road_type:
                    self.list_node_on_same_road_type.append(index)
                # list node on other road types
                else:
                    self.list_node_on_other_road_type.append(index)

            # prefer to choose same road name first
            if len(self.list_node_on_same_road_name) != 0:
                self.next_node_index = self.list_node_on_same_road_name[0]
            # if not, choose same road type
            elif len(self.list_node_on_same_road_type) != 0:
                self.next_node_index = self.random.choice(
                    self.list_node_on_same_road_type)
            # if not, choose the other road type
            elif len(self.list_node_on_other_road_type) != 0:
                self.next_node_index = self.random.choice(
                    self.list_node_on_other_road_type)

        self._update_road_info()
        self._check_next_node_in_same_or_next_cell()
        self._make_move()

    def intersection2(self):
        # STORE INTERSECTION FOR MEMORY
        # intersection memory
        self.memory_node_osmid.append(self.current_node_index)
        self.memory_node_coord.append(self.current_node_position)

        # dead end memory
        if len(self.model.graph_edges.loc[self.current_node_index]['osmid']) == 1 and self.current_node_index not in self.init_road_index:
            self.memory_deadend_osmid.append(self.current_node_index)
            self.memory_deadend_coord.append(self.current_node_position)

        # find all possible nodes around
        self.possible_next_node_index = self.model.node_connections[self.current_node_index]

        # ignore previous road
        self.possible_next_node_index_copy = [
            index for index in self.possible_next_node_index if index != self.previous_node_index]

        # GET LIST ROADS AROUND HAVING DIFFERENT TYPE TO TURN, IF NO DIFFERENT TYPE, THEN LIST INCLUDE SAME TYPE NOT SAME NAME (NOT STRAIGHT), not including previous road
        self.type_roads_around = []
        self.type_roads_around_nodes = []

        if len(self.possible_next_node_index_copy) != 0:
            # IGNORE STRAIGHT ROAD (ROAD HAS SAME NAME)
            self.possible_next_node_index_copy3 = []
            for index in self.possible_next_node_index_copy:
                if self.model.graph_edges.loc[(self.current_node_index, index, 0)]['name'] != self.current_road_name:
                    self.possible_next_node_index_copy3.append(index)

            for index in self.possible_next_node_index_copy3:
                type_road = self.model.graph_edges.loc[(
                    self.current_node_index, index, 0)]['highway']
                self.type_roads_around.append(type_road)
                self.type_roads_around_nodes.append(index)

        # GET OUT OF A STRAIGHT ROAD THAT HAS LENGTH < 300
        if self.straight_road_length < 300 and self.endpoint1 != None and self.endpoint2 != None:
            if len(self.possible_next_node_index_copy) > 0:
                self.next_node_index = self.random.choice(
                    self.possible_next_node_index_copy)
                self._update_endpoint_when_make_a_turn()
            else:
                self.next_node_index = self.random.choice(
                    self.possible_next_node_index)

        # POSSIBILITY TO TURN WHILE RUNNING STRAIGHT
        # turn to tertiary
        # rate != None, have tertiary road to turn, fall within rate
        elif self.pr_turn_on_ter != None and ('tertiary' in self.type_roads_around) and self.random.random() < self.pr_turn_on_ter:
            index = self.type_roads_around.index('tertiary')
            self.next_node_index = self.type_roads_around_nodes[index]
            self._update_endpoint_when_make_a_turn()

        # turn to secondary
        # rate != None, have secondary road to turn, fall within rate
        elif self.pr_turn_on_sec != None and ('secondary' in self.type_roads_around) and self.random.random() < self.pr_turn_on_sec:
            index = self.type_roads_around.index('secondary')
            self.next_node_index = self.type_roads_around_nodes[index]
            self._update_endpoint_when_make_a_turn()

        # turn to residential
        # rate != None, have residential road to turn, fall within rate
        elif self.pr_turn_on_res != None and ('residential' in self.type_roads_around) and self.random.random() < self.pr_turn_on_res:
            index = self.type_roads_around.index('residential')
            self.next_node_index = self.type_roads_around_nodes[index]
            self._update_endpoint_when_make_a_turn()

        # turn to primary
        # rate != None, have primary road to turn, fall within rate
        elif self.pr_turn_on_pri != None and ('primary' in self.type_roads_around) and self.random.random() < self.pr_turn_on_pri:
            index = self.type_roads_around.index('primary')
            self.next_node_index = self.type_roads_around_nodes[index]
            self._update_endpoint_when_make_a_turn()

        # ENCOUNTER TRAFFIC SIGNALS, MAKE A U TURN OR GO STRAIGHT
        elif self.model.graph_nodes.loc[self.current_node_index]['highway'] == 'traffic_signals':

            # go straight if fall within the possibility rate
            self.list_straight_road = [index for index in self.possible_next_node_index_copy[:] if self.model.graph_edges.loc[(
                self.current_node_index, index, 0)]['name'] == self.current_road_name]
            if len(self.list_straight_road) != 0 and self.random.random() < self.pr_go_straight_at_traffic_signals:
                self.next_node_index = self.list_straight_road[0]

            # otherwise, make U-turn
            else:
                self._set_node_to_make_u_turn_on_straight_road()
                # update endpoint
                self._update_endpoint_when_make_u_turn()

        # CHOOSE NEXT NODE IN THE SAME ROAD (straight road)
        # if at dead end for first time --> u turn (intersection of 1)
        elif len(self.possible_next_node_index_copy) == 0 and len(self.model.graph_edges.loc[self.current_node_index]['osmid']) == 1:
            self.next_node_index = self.previous_node_index

            # Store one endpoint if not set yet
            self._update_endpoint_when_make_u_turn()

        else:
             # choose road forward (straight road)
            have_forward_road = False
            for index in self.possible_next_node_index_copy:
                self.current_road_index = (self.current_node_index, index, 0)
                # list node on current road name
                if self.model.graph_edges.loc[self.current_road_index]['name'] == self.current_road_name:
                    self.next_node_index = index
                    have_forward_road = True
                    break
            # at intersection of 3, previous road is same road, 2 other roads are different roads. Therefore, U-turn
            if not have_forward_road:
                self._set_node_to_make_u_turn_on_straight_road()

                # Store one endpoint if not set yet
                self._update_endpoint_when_make_u_turn()

        self._update_road_info()
        self._check_next_node_in_same_or_next_cell()
        self._make_move()

    def _update_endpoint_when_make_u_turn(self):
        if self.endpoint1 == None:
            self.endpoint1 = self.current_node_index
            self.start_from_one_endpoint = True
        elif self.endpoint2 == None:
            self.endpoint2 = self.current_node_index
            self.start_from_one_endpoint = False

    def _update_endpoint_when_make_a_turn(self):
        # reset endpoint for new road
        self.straight_road_length = 0
        self.endpoint1 = None
        self.endpoint2 = None
        # since runner could turn to the middle of road
        self.start_from_one_endpoint = False

    def _set_node_to_make_u_turn_on_straight_road(self):
        # U-turn on any road
        if self.previous_node_index != None:
            self.next_node_index = self.previous_node_index
        # U-turn on the init road
        elif self.current_node_index == self.current_road_index[0]:
            self.next_node_index = self.current_road_index[1]
        elif self.current_node_index == self.current_road_index[1]:
            self.next_node_index = self.current_road_index[0]

    def intersection3(self):

        # Change to mode running on park once runner stand on the node of park
        if self.current_node_index == self.target_node_coming_park:
            self.on_the_park = True

        # Reset target node while running on park once runner's on the target node
        if self.current_node_index == self.target_node_running_around_park:
            self.target_node_running_around_park = None

        # STORE INTERSECTION FOR MEMORY
        # intersection memory
        self.memory_node_osmid.append(self.current_node_index)
        self.memory_node_coord.append(self.current_node_position)

        # dead end memory
        if len(self.model.graph_edges.loc[self.current_node_index]['osmid']) == 1 and self.current_node_index not in self.init_road_index:
            self.memory_deadend_osmid.append(self.current_node_index)
            self.memory_deadend_coord.append(self.current_node_position)

        # FIND ALL POSSIBLE ROADS AROUND CURRENT POSITION
        self.possible_next_node_index = self.model.node_connections[self.current_node_index]
        # ignore previous road starting from the second intersection from the point want to go home
        if len(self.memory_node_osmid_way_home) == 1:
            self.possible_next_node_index_copy = self.possible_next_node_index[:]
        else:
            self.possible_next_node_index_copy = [
                index for index in self.possible_next_node_index if index != self.previous_node_index]

        # got to the node of park on the initial road
        if self.current_node_index in self.model.footway_all_nodes:
            self.on_the_park = True

        # ON THE WAY TO PARK
        if not self.on_the_park:
            # if it just start, set the next node index as the current node index
            if self.current_node_index == None:
                self.current_node_index = self.next_node_index

            # find the shortest path and the nodes of that
            shortest_length = None
            for index in self.model.footway_nodes_access:
                length = nx.shortest_path_length(
                    self.model.graph, self.current_node_index, index, weight='length')
                if shortest_length == None:
                    shortest_length = length
                    self.target_node_coming_park = index
                elif length < shortest_length:
                    shortest_length = length
                    self.target_node_coming_park = index

            # get shortest path to that node
            self.shortest_path = nx.shortest_path(
                self.model.graph, self.current_node_index, self.target_node_coming_park, weight='length')

            # choose to follow the shortest path
            if self.random.random() > self.possibility_change_way_park:
                self.next_node_index = self.shortest_path[1]
            # if not, choose one of the way around that current node
            else:
                if len(self.possible_next_node_index_copy) != 0:
                    self.next_node_index = self.random.choice(
                        self.possible_next_node_index_copy)
                else:
                    self.next_node_index = self.random.choice(
                        self.possible_next_node_index)

        # GET TO THE PARK ALREADY AND RUNNING AROUND
        elif self.on_the_park:

            # set the set node around the current node on park if don't have yet
            if self.current_set_node_on_park == None:
                if self.current_node_index in self.model.footway_nodes_set1:
                    self.current_set_node_on_park = self.model.footway_nodes_set1[:]
                elif self.current_node_index in self.model.footway_nodes_set2:
                    self.current_set_node_on_park = self.model.footway_nodes_set2[:]

            # set distance running on park if don't have yet
            if self.distance_run_around_park == None:
                self._set_distance_run_around_park()

            # choose next cell from the set data and avoid previous road as much as it can
            if self.target_node_running_around_park == None:
                self.target_node_running_around_park = self.random.choice(
                    [index for index in self.current_set_node_on_park if index != self.current_node_index and index != self.previous_node_index])

            self.possible_next_node_index = nx.shortest_path(
                self.model.graph, self.current_node_index, self.target_node_running_around_park, weight='length')
            self.next_node_index = self.possible_next_node_index[1]

        self._update_road_info()
        self._check_next_node_in_same_or_next_cell()
        self._make_move()

        # REACH THE DISTANCE SET TO RUN AROUND PARK, THEN GO HOME OR GET OUT OF PARK
        if self.distance_will_get_out_park != None and self.distance_gone > self.distance_will_get_out_park and not self.want_to_go_home:
            self.preference = 'preference2'

    def intersection4(self):
        # STORE INTERSECTION FOR MEMORY
        # intersection memory
        self.memory_node_osmid.append(self.current_node_index)
        self.memory_node_coord.append(self.current_node_position)

        # dead end memory
        if len(self.model.graph_edges.loc[self.current_node_index]['osmid']) == 1 and self.current_node_index not in self.init_road_index:
            self.memory_deadend_osmid.append(self.current_node_index)
            self.memory_deadend_coord.append(self.current_node_position)

        # on way home memory
        if not self.begin_going_home:  # ignore the first starting point going home
            self.memory_node_osmid_way_home.append(self.current_node_index)
            self.memory_node_coord_way_home.append(self.current_node_position)
        self.begin_going_home = False

        # CHOOSE AN INDEX FROM INITIAL ROAD INDEX AS A TARGET POINT TO GET BACK HOME
        if self.init_index == None:
            self.init_index = self.random.choice(
                [self.init_road_index[0], self.init_road_index[1]])

        # FIND ALL POSSIBLE ROADS AROUND CURRENT POSITION
        self.possible_next_node_index = self.model.node_connections[self.current_node_index]
        # ignore previous road starting from the second intersection from the point want to go home
        if len(self.memory_node_osmid_way_home) == 1:
            self.possible_next_node_index_copy = self.possible_next_node_index[:]
        else:
            self.possible_next_node_index_copy = [
                index for index in self.possible_next_node_index if index != self.previous_node_index]

        # stand on the init_index
        if self.current_node_index == self.init_index:
            u, v, k = self.init_road_index
            if self.current_node_index == u:
                self.next_node_index = v
            else:
                self.next_node_index = u

        # choose to follow the shortest path
        elif self.random.random() > self.possibility_change_way_home:
            self.shortest_path = nx.shortest_path(
                self.model.graph, self.current_node_index, self.init_index, weight='length')
            self.next_node_index = self.shortest_path[1]

        # change, want to explore/try a section of road
        # select randomly a road for this step
        else:
            if len(self.possible_next_node_index_copy) > 0:
                self.next_node_index = self.random.choice(
                    self.possible_next_node_index_copy)
            else:
                self.next_node_index = self.random.choice(
                    self.possible_next_node_index)

        self._update_road_info()
        self._check_next_node_in_same_or_next_cell()
        self._make_move()

    def _update_road_info(self):
        # update current_road_index and next_node_position
        self.current_road_index = (
            self.current_node_index, self.next_node_index, 0)
        self.next_node_position = self.model.cell_of_node[self.next_node_index]

        # UPDATE NEW ROAD INFO
        self.current_road_name = self.model.graph_edges.loc[self.current_road_index]['name']
        self.current_road_type = self.model.graph_edges.loc[self.current_road_index]['highway']
        self.current_road_cells = self.model.cells_of_edge[self.current_road_index]
        self.current_road_length = self.model.graph_edges.loc[self.current_road_index]['length']

        self.current_cell_index_on_roadset = 0

    def _check_next_node_in_same_or_next_cell(self):
        # WHAT IF THE NEXT NODE IS IN THE SAME OR NEXT CELL?
        if len(self.current_road_cells) == 0:
            self.next_position = self.next_node_position
            self.switch_previous_and_current_node_index()
            self._adding_distance_goal()
            # keep state
        else:
            self.next_position = self.current_road_cells[self.current_cell_index_on_roadset]
            # CHANGE STATE BACK TO _continue_forward
            self.state = '_continue_forward'

    def _make_move(self):
        # MAKE A MOVE
        self.to_node = 'v'
        self._move_agent_update_attributes()

    def _adding_distance_goal(self):
        # ADDING DISTANCE GONE
        if self.start_on_road:
            if self.num_cells_gone_on_road == 0:
                self.num_cells_gone_on_road = 1

            self.amount_added = round(((self.num_cells_gone_on_road / len(
                self.current_road_cells)) * self.current_road_length), 0)
            self.distance_gone += self.amount_added
            self.start_on_road = False
        else:
            self.amount_added = self.current_road_length
            self.distance_gone += self.amount_added

        # CHECK TO SEE IF IT WILL RUNNER GETS FARER OR CLOSER FROM INIT POS & UPDATE DISTANCE BACK HOME
        a, b = self.init_position
        x, y = self.next_node_position

        # calculate to find appro. distance
        self.check_closer_or_farer = (a - x)**2 + (b - y)**2

        # set previous distance back home
        self.estimate_distance_back_home_previous = self.estimate_distance_back_home
        # check to see add or subtract
        if self.check_closer_or_farer > self.estimate_distance_cell_to_init_point:
            self.estimate_distance_back_home += self.amount_added
        elif self.check_closer_or_farer < self.estimate_distance_cell_to_init_point:
            self.estimate_distance_back_home -= self.amount_added

        # set new estimate distance cell to init point by the new number
        self.estimate_distance_cell_to_init_point = self.check_closer_or_farer

        # UPDATE EDGES' USING MEMORY
        self.model.memory_edge_using[self.current_road_index] += 1

        # ADD LENGTH FOR STRAIGHT ROAD
        self._add_length_straight_road()

    def _add_length_straight_road(self):
        # START ADDING DISTANCE FROM ENDPOINT 1 OF A STRAIGHT ROAD
        if self.start_from_one_endpoint:
            self.straight_road_length += self.amount_added

    def _move_agent_update_attributes(self):
        x, y = self.next_position

        # IF JUST STARTS ON A ROAD, NEED TO ADD NUM OF CELLS GONE TO CALCULATE APPRO. LENGTH
        if self.start_on_road:
            self.num_cells_gone_on_road += 1

        # MOVE AGENT
        self.model.grid.move_agent(self, self.next_position)

        # UPDATE THE HEATMAP FOR EVERYTIME IT GOES TO A NEW LOCATION
        self.model.heatmap_data[y][x] += 1

        # SET WANT TO GO HOME MODE ONCE DISTANCE GONE + DISTANCE BACK HOME > DISTANCE GOAL
        if (self.distance_gone + self.estimate_distance_back_home) >= self.distance_goal:
            # self.state = 'rest'
            self.want_to_go_home = True
            self.begin_going_home = True
            self.preference = 'preference4'
