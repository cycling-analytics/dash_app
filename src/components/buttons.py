from dash import html
import dash_bootstrap_components as dbc

def create_buttons():
    component = html.Div([
        html.Div(dbc.RadioItems(className='btn-group', inputClassName='btn-check', labelClassName='btn btn-outline-light', labelCheckedClassName='btn btn-light', options=[{"label": "Plots", "value": 1}, {"label": "Table", "value": 2}], value=1), style={'width': 206}),
        html.Div(dbc.Button(children="About", className="btn btn-info", n_clicks=0), style={'width': 104})
    ], style={'marginLeft': '15px', 'marginRight': '15px', 'display': 'flex'})
    return component
