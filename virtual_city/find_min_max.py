import osmnx as ox
import networkx as nx
import geopandas
import pandas as pd
from pylab import *
print('EXECUTING')

# Get graph
g = ox.graph_from_place(
    'Brentwood - Darlington, Portland, Oregon, USA', network_type='all')

# tranfer to GDF
g_gdf_nodes, g_gdf_edges = ox.graph_to_gdfs(g)

# transfer to data fram
g_dataframe_nodes = pd.DataFrame(g_gdf_nodes)
g_dataframe_edges = pd.DataFrame(g_gdf_edges)

longitude_min = g_dataframe_nodes.x.min()
longitude_max = g_dataframe_nodes.x.max()
latitude_min = g_dataframe_nodes.y.min()
latitude_max = g_dataframe_nodes.y.max()
print('Longitude min: ', longitude_min)
print('Longitude max: ', longitude_max)
print('Latitude min: ', latitude_min)
print('Latitude max: ', latitude_max)
