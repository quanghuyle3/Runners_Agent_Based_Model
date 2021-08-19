from virtual_world import VirtualWorldModel

from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer


def cell(agent):
    portrayal = {'Shape': 'rect',
                 'Layer': 0,
                 'w': 1,
                 'h': 1,
                 'Filled': 'true'}

    if agent.type == 'house':
        portrayal['Color'] = '#C9160A'
    elif agent.type == 'road':
        portrayal['Color'] = '#D0DC19'
    elif agent.type == 'trail':
        portrayal['Color'] = '#C98C0A'
    elif agent.type == 'forest':
        portrayal['Color'] = '#237308'
    elif agent.type == 'grass':
        portrayal['Color'] = '#4ECA24'


<< << << < Updated upstream
    elif agent.type == 'runner':
== == == =
    elif agent.type == 'type1':
>>>>>> > Stashed changes
        portrayal['Shape'] = 'circle'
        portrayal['r'] = '0.7'
        portrayal['Layer'] = 1
        portrayal['Color'] = 'black'

    elif agent.type == 'type2':
        portrayal['Shape'] = 'circle'
        portrayal['r'] = '0.7'
        portrayal['Layer'] = 2
        portrayal['Color'] = 'blue'

    return portrayal


grid = CanvasGrid(cell, 50, 50, 600, 600)
# chart = ChartModule([{'Label': 'Num_mov_agents', 'Color': 'Black'}])

<<<<<<< Updated upstream
server = ModularServer(VirtualWorldModel, [grid], "Virtual World", {'N': 1,
=======
server = ModularServer(VirtualWorldModel, [grid], "Virtual World", {'N': 10,
>>>>>>> Stashed changes
                                                                    'width': 50, 'height': 50})
server.port = 8000

server.launch()
