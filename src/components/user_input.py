from dash import html, dcc

def create_select_leader():
    component = html.Div([
        html.Div([
            html.H2('leader:'),
            dcc.Dropdown(
                id='leader-dropdown',
                placeholder='Select leader name',
                className="customDropdown"
            )
        ])
    ],
        style={
            'marginLeft': 15,
            'marginRight': 15,
            'marginRop': 30
        }
    )

    return component


def create_select_start():
    component = html.Div([
        html.H2('Select the start time (hour, minute, second):'),
        #dcc.Slider(0,0, id='time-slider', step=1),
        dcc.Input(id='start_hour_input', type='number', value='0', min='0', max='23', step='1', ),
        dcc.Input(id='start_minutes_input', type='number', value='0', min='0', max='59', step='1', ),
        dcc.Input(id='start_seconds_input', type='number', value='0', min='0', max='59', step='1', ),
        #html.Button('Set starting hour', id='start_button', n_clicks=0)
    ],
        style={
            'marginLeft': 15,
            'marginRight': 15,
            'marginRop': 30
        }
    )

    return component