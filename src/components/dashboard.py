from dash import html, dcc

from components.map import create_map


def create_dashboard():
    component = html.Div([
        create_map(),
        dcc.Graph(id='kilojoules-graph', style={'display': 'none'}),
        dcc.Graph(id='follow_the_leader_plot', style={'display': 'none'}),
        dcc.Graph(id='speed_comparison-graph', style={'display': 'none'}),
        html.Div(children=[], id='output_table'),
        html.Div(children=[], id='download_excel_button'),
        html.Button('Download to excel', id='download-table', style={'display': 'none'}),
        dcc.Download(id='download-table_xlsx')
    ], style={'width': 990})
    return component
