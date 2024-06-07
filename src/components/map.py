import dash_leaflet as dl

def create_map():
    component = dl.Map(id='map', style={'width': '1000px', 'height': '500px'}, center=(50, 0), zoom=14, children=[])
    return component

