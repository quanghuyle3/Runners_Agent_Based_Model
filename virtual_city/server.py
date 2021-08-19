from virtual_city import VirtualCityModel

from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer


def cell(agent):
    portrayal = {'Shape': 'rect',
                 'Layer': 0,
                 'w': 1,
                 'h': 1,
                 'Filled': 'true',
                 'Color': 'green'}

    if agent.type == 'runner' and agent.gender == 'male':
        portrayal['Shape'] = 'circle'
        portrayal['r'] = '0.8'
        portrayal['Layer'] = 1
        portrayal['Color'] = 'red'
    elif agent.type == 'runner' and agent.gender == 'female':
        portrayal['Shape'] = 'circle'
        portrayal['r'] = '0.8'
        portrayal['Layer'] = 1
        portrayal['Color'] = 'white'
    elif agent.type == 'traffic_signals':
        portrayal['Color'] = '#07942A'       # light cyan
    elif agent.type == 'intersection':
        portrayal['Color'] = 'black'
    elif agent.type == 'primary':
        portrayal['Color'] = 'blue'
    elif agent.type == 'secondary':
        portrayal['Color'] = 'purple'
    elif agent.type == 'residential':
        portrayal['Color'] = '#D0DC19'
    elif agent.type == 'tertiary':
        portrayal['Color'] = 'orange'
    elif agent.type == 'footway':
        portrayal['Color'] = '#07942A'
    elif agent.type == 'service':
        portrayal['Color'] = 'cyan'

    elif agent.type == 'path':
        portrayal['Color'] = 'pink'
    elif agent.type == 'grass':
        portrayal['Color'] = '#4ECA24'

    return portrayal


grid = CanvasGrid(cell, 202, 84, 2020, 840)
chart1 = ChartModule([{'Label': 'Preference 1', 'Color': 'Blue'}, {
                     'Label': 'Preference 2', 'Color': 'Cyan'}, {'Label': 'Preference 3', 'Color': 'Green'}])
chart2 = ChartModule([{'Label': 'Going home (Pref 4)', 'Color': 'Yellow'}, {
                     'Label': 'Agents got home', 'Color': 'Red'}])
server = ModularServer(VirtualCityModel, [grid, chart1, chart2], "Brentwood - Darlington", {'N': 500,
                                                                                            'width': 202, 'height': 84})
# server.port = 8521

server.launch()
