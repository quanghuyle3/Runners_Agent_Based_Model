import osmnx as ox
import pandas as pd

print('EXECUTING')
g = ox.graph_from_place(
    'Brentwood - Darlington, Portland, Oregon, USA', network_type='all')

# Tranfer to GeoDataFrame
g_gdf_nodes, g_gdf_edges = ox.graph_to_gdfs(g)


# Transfer to dataframe
g_dataframe_nodes = pd.DataFrame(g_gdf_nodes)
g_dataframe_edges = pd.DataFrame(g_gdf_edges)

# Write data to csv files
# g_dataframe_nodes.to_csv('Nodes_data_from_network.csv')
# g_dataframe_edges.to_csv('Edges_data_from_network.csv')

# plot graph
ox.plot_graph(g)
