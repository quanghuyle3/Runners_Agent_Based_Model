# Agent-based Activity Generation of Runners for City Infrastructure Planning
In this project, an agent-based model is developed by using [MESA framework] in Python 3+ to generate the daily activities for a population of people. Specifically, focusing on runners and generating a set of routes that typical runners would take on their daily runs. A heat map is automatically created at the end of the simulation to compare with the Strava heat map.

## Features
### Simple virtual world
- Create a simple grid world to represent a simple world which has normal roads, trails, forests, houses, and grass.
- Initialize a number of runners to roam around the map and follow the state machines of its corresponding behaviors.

### Virtual city
- Transform an actual street network dowloaded by [OSMnx package] of a neighborhood in Portland city into a grid world.
- Encode several real behaviors of runners into this agent-based model and simulate it with 500 agents on the grid world.
- Generate a heat map at the end to identify roads that are used by runners and the level of being used.

## Framework/Package used in Python
- MESA
- OSMnx
- NetworkX
- Pandas
- Numpy
- Matplotlib
- Seaborn

## Application
This model is an example to study about the runners of a neighborhood in Portland city. However, this is transferable and could be used for other areas as all street networks data from [OpenStreetMap] are available and could be downloaded by using the [OSMnx package].

   [MESA framework]: <https://mesa.readthedocs.io/en/master/>
   [OpenStreetMap]: <https://www.openstreetmap.org/>
   [OSMnx package]: <https://osmnx.readthedocs.io/en/stable/>
