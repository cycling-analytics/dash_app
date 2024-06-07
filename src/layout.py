from dash import html, dcc
import dash_bootstrap_components as dbc
from components.title import create_title
from components.buttons import create_buttons
from components.upload import create_upload, create_upload_rider_info
from components.user_input import create_select_leader, create_select_start
from components.dashboard import create_dashboard


def create_layout():
    component = dbc.Container([
        html.Div(
            [
                create_title(),
                #create_buttons(),
                create_upload(),
                create_upload_rider_info(),
                dcc.Loading(id="loading", type="default", children= create_select_leader()),
                create_select_start(),
                html.Button('Process', id='process-button', n_clicks=0),
            ],
            style={'width': 300, 'marginLeft': 35, 'marginTop': 35, 'marginBottom': 35}
        ),
        html.Div(
            [
                create_dashboard()
            ],
            style={'width': 990, 'marginTop': 35, 'marginRight': 35, 'marginBottom': 35, 'display': 'flex'})
    ],
        fluid=True,
        style={'display': 'flex'},
        className='dashboard-container')

    return component
