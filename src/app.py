import base64
import gzip
from datetime import datetime, timedelta

import pandas as pd
import yaml
from dash import Dash, html, dcc, callback, Output, Input, State, dash_table
import dash_bootstrap_components as dbc
from garmin_fit_sdk import Stream, Decoder
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_leaflet as dl

from aux import build_df, add_best_power_values, compute_avg_NP


def create_title():
    component = html.Div([
        html.H1([
            html.Span("Analytics"),
            html.Br(),
            html.Span("Dashboard")
        ]),
        html.P("This dashboard prototype shows the initial functionality 1")
    ],
        style={
            "verticalAlignment": "top",
            "height": 260
        })

    return component


def create_buttons():
    print('hola')
    component = html.Div(
        [
            html.Div(dbc.RadioItems(
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-light',
                labelCheckedClassName='btn btn-light',
                options=[
                    {"label": "Plots", "value": 1},
                    {"label": "Table", "value": 2}
                ],
                value=1
            ),
                style={'width': 206}),
            html.Div(
                dbc.Button(
                    children="About",
                    className="btn btn-info",
                    n_clicks=0
                ),
                style={'width': 104})
        ],
        style={
            'marginLeft': '15px',
            'marginRight': '15px',
            'display': 'flex'
        })

    return component


def create_upload():
    component = html.Div([
        html.H2('Race files'),
        dcc.Upload(
            id='upload-fit-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select fit.gz Files')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px',
                'color': 'white'
            },
            # Allow multiple files to be uploaded
            multiple=True
        )])

    return component


def create_upload_rider_info():
    component = html.Div([
        html.H2("Rider Info"),
        dcc.Upload(
            id='upload-riders-data',
            children=html.Div([
                html.A('Select file with riders info')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px',
                'color': 'white'
            },
            # Allow multiple files to be uploaded
            multiple=False
        )])

    return component


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


def create_riders_checklist():
    component = dcc.Checklist(
        id='riders_checklist',
        options=[],
        value=[],
        style={
            'width': '100%',
            'marginLeft': '15px',
        }
    )

    return component


def create_map():
    component = dl.Map(
        id='map',
        style={'width': '1000px', 'height': '500px'},
        center=(50, 0),  # Initial position
        zoom=14,  # Initial zoom level
        children=[]
    )

    return component


def create_dashboard():
    component = html.Div([
        create_map(),
        dcc.Graph(id='kilojoules-graph', style={'display': 'none'}),
        dcc.Graph(id='follow_the_leader_plot', style={'display': 'none'}),
        dcc.Graph(id='speed_comparison-graph', style={'display': 'none'}),
        html.Div(children=[], id='output_table'),
        html.Div(children=[], id='download_excel_button'),
        html.Button('Download to excel', id='download-table', style={'display': 'none'}),
        dcc.Download(id='download-table_xlsx'),
    ],
        style={'width': 990},
    )

    return component


def create_layout():
    component = dbc.Container([
        html.Div([create_title(), create_buttons(),
                  create_upload(), create_upload_rider_info(), create_select_leader(),
                  create_select_start(), create_riders_checklist(), ],
                 style={
                     'width': 300,
                     'marginLeft': 35,
                     'marginTop': 35,
                     'marginBottom': 35
                 }),
        html.Div(
            [create_dashboard(),
             ],
            #html.Div(style={'width': 200})],
            style={
                'width': 990,
                'marginTop': 35,
                'marginRight': 35,
                'marginBottom': 35,
                'display': 'flex'
            })
    ],
        fluid=True,
        style={'display': 'flex'},
        className='dashboard-container')

    return component


############# Callbacks

@callback(Output('memory-rides', 'data', allow_duplicate=True),
          Output('memory-corrected_rides', 'data', allow_duplicate=True),
          Output('leader-dropdown', 'options'),
          Output('riders_checklist', 'options'),
          Output('riders_checklist', 'value'),
          Input('upload-fit-data', 'contents'),
          State('upload-fit-data', 'filename'),
          prevent_initial_call=True)
def update_data(list_of_contents, list_of_names):
    rides_dict_df = {}

    if list_of_contents is not None:
        data = parse_contents(list_of_contents, list_of_names)

        rides_dict_df = {}
        for name, info in data.items():
            rides_dict_df[name] = build_df(info['ride'], info['events']).to_dict('records')

        list_of_names = list(rides_dict_df.keys())
    return rides_dict_df, rides_dict_df, list_of_names, list_of_names, list_of_names


@callback(Output('memory-riders-data', 'data', allow_duplicate=True),
          Input('upload-riders-data', 'contents'),
          State('upload-riders-data', 'filename'),
          prevent_initial_call=True)
def update_riders_data(content, name):
    riders_dict = {}
    if content is not None:
        content_type, content_string = content.split(',')
        decoded = base64.b64decode(content_string)

        # Assuming the uploaded file is YAML
        riders_dict = yaml.safe_load(decoded)

    return riders_dict


@callback(
    Output('map', 'children'),
    Output('map', 'center'),
    Input('memory-corrected_rides', 'data'),
)
def update_map(rides):
    children = []
    center = (0,0)
    if (rides is not None) and (len(rides) > 0):
        #       rides_corrected = {name: pd.DataFrame(data) for name, data in rides.items()}
        mean_starting_lat = sum([data[0]["position_lat"] for _, data in rides.items()])
        mean_starting_lat /= len(rides)

        mean_starting_long = sum([data[0]["position_long"] for _, data in rides.items()])
        mean_starting_long /= len(rides)

        center = ( mean_starting_lat, mean_starting_long)

        marker_coords = [
            (data[0]["position_lat"], data[0]["position_long"])
            for _, data in rides.items()
        ]

        children = [
            dl.TileLayer(),  # Base layer that provides the map
            dl.LayerGroup([
                dl.Marker(position=coord, children=[
                    dl.Tooltip(f"{name}")
                ]) for name, coord in zip(rides.keys(), marker_coords)
            ])
        ]

    return children, center


@callback(
    Output('output_table', 'children'),
    Output('memory-comparative_table', 'data', allow_duplicate=True),
    Input('memory-corrected_rides', 'data'),
    Input('memory-riders-data', 'data'),
    prevent_initial_call=True,
)
def update_comparative_table(rides, riders_data):
    table = []
    comparative_table = {}

    if (rides is not None) and (riders_data is not None):
        df_to_show = build_metrics(rides, riders_data)
        table = [build_htmlTable(df_to_show)]

        comparative_table = df_to_show.to_dict("records")

    return table, comparative_table


@callback(
    Output('download-table', 'style'),
    Input('output_table', 'children'),
    prevent_initial_call=True,
)
def show_download_button(output_table):
    return {'display': 'flex'}


@callback(
    Output('follow_the_leader_plot', 'figure'),
    Output('follow_the_leader_plot', 'style'),
    Input('memory-corrected_rides', 'data'),
    Input('leader-dropdown', 'value'),
    Input('riders_checklist', 'value'),
)
def update_leader_comparative(rides, leader, selected_riders):
    fig = make_subplots(specs=[[{"secondary_y": True}]])  #go.Figure()
    style = {'display': 'none'}

    if (rides is not None and rides != {}) and (leader is not None and leader != {}):
        style = {'display': 'flex'}
        # Initialize an empty DataFrame to store the differences
        #differences_df = pd.DataFrame()

        reference_df = pd.DataFrame(rides[leader])
        reference_df.timestamp = pd.to_datetime(reference_df.timestamp)

        #Add activity profile to the graph

        fig.add_trace(
            go.Scatter(x=reference_df.distance / 1000, y=reference_df.altitude, mode='lines', name='altitude'),
            secondary_y=True
        )

        for rider in selected_riders:
            rider_data = rides[rider]
            rider_df = pd.DataFrame(rider_data)
            rider_df.timestamp = pd.to_datetime(rider_df.timestamp)

            max_length = min(rider_df.shape[0], reference_df.shape[0])

            differences = rider_df.iloc[:max_length]['distance'].values - reference_df.iloc[:max_length][
                'distance'].values

            fig.add_trace(
                go.Scatter(x=reference_df.distance / 1000, y=differences, mode='lines', name=rider),
                secondary_y=False
            )

        fig.update_layout(
            title_text="<b>Distance with respect to the Leader</b>"
        )

        # Set x-axis title
        fig.update_xaxes(title_text="Distance (Km)")

        # Set y-axes titles
        fig.update_yaxes(title_text="Difference (meters)", secondary_y=False)
        fig.update_yaxes(title_text="Altitude (meters)", secondary_y=True)

    return fig, style


@callback(
    Output('speed_comparison-graph', 'figure'),
    Output('speed_comparison-graph', 'style'),
    Input('memory-corrected_rides', 'data'),
    prevent_initial_call=True,
)
def update_speed_comparison(rides):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    style = {'display': 'none'}

    if (rides is not None) and (rides != {}):
        style = {'display': 'flex'}

        profile_plotted = False
        for rider, data in rides.items():
            df = pd.DataFrame(data)
            df.timestamp = pd.to_datetime(df.timestamp)

            if not profile_plotted:
                profile_plotted = True
                fig.add_trace(
                    go.Scatter(x=df['distance'] / 1000, y=df.altitude, mode='lines', name='Altitude'),
                    secondary_y=True
                )

            fig.add_trace(
                go.Scatter(x=df.distance / 1000, y=df.speed, mode='lines', name=rider),
                secondary_y=False
            )

        # Add figure title
        fig.update_layout(
            title_text="<b>Speed</b>"
        )

        # Set x-axis title
        fig.update_xaxes(title_text="Distance (Km)")

        # Set y-axes titles
        fig.update_yaxes(title_text="Speed (Km/h)", secondary_y=False)
        fig.update_yaxes(title_text="Altitude (meters)", secondary_y=True)

    return fig, style


@callback(
    Output('kilojoules-graph', 'figure'),
    Output('kilojoules-graph', 'style'),
    Input('memory-corrected_rides', 'data'),
    prevent_initial_call=True
)
def update_kilojoules_per_hour(rides):
    fig = make_subplots(specs=[[{"secondary_y": True}]])  # go.Figure()
    style = {'display': 'none'}
    if rides is not None and rides != {}:
        style = {'display': 'flex'}

        profile_plotted = False
        dfs_with_kJ = {}
        for rider, data in rides.items():
            df = add_kilojoules_per_hour(data)

            if not profile_plotted:
                profile_plotted = True
                fig.add_trace(
                    go.Scatter(x=df['distance'] / 1000, y=df['altitude'], mode='lines', name='Altitude'),
                    secondary_y=True
                )

            fig.add_trace(
                go.Scatter(x=df['distance'] / 1000, y=df['kilojoules_last_hour'], mode='lines', name=rider),
                secondary_y=False
            )

        # Add figure title
        fig.update_layout(
            title_text="<b> Spent energy in the last hour </b>"
        )

        # Set x-axis title
        fig.update_xaxes(title_text="Distance (Km)")

        # Set y-axes titles
        fig.update_yaxes(title_text="Energy (kJ)", secondary_y=False)
        fig.update_yaxes(title_text="Altitude (meters)", secondary_y=True)

    return fig, style


@callback(
    Output('start_hour_input', 'value'),
    Output('start_minutes_input', 'value'),
    Output('start_seconds_input', 'value'),
    Input('memory-corrected_rides', 'data'),
    prevent_initial_call=True
)
def update_start_time_div(rides):
    #start_time_seconds = 0
    #end_time_seconds = 0
    #marks = {}
    min_timestamp = datetime.now().timestamp()
    if rides is not None and rides != {}:
        min_times = []
        for rider, rider_data in rides.items():
            i = 0
            while rider_data[i]['timestamp'] is None:
                i += 1

            str_time = rider_data[i]['timestamp']
            min_times.append(datetime.fromisoformat(str_time))

        # We can compare only from the latest starting hour
        min_timestamp = max(min_times)

        # Calculate the range for the slider
        # Convert time to seconds from start of the day for simplicity
        # start_time_seconds = min_timestamp.hour * 3600 + min_timestamp.minute * 60 + min_timestamp.second
        # end_time_seconds = max_timestamp.hour * 3600 + max_timestamp.minute * 60 + max_timestamp.second

        # marks = {
        #     t: f"{t // 3600:02d}:{(t % 3600) // 60:02d}:{t % 60:02d}" for t in
        #     range(start_time_seconds, end_time_seconds + 1, 900)
        # }  # Marks every 15 minutes

        # memory['date'] = min_timestamp.date()

    return min_timestamp.hour, min_timestamp.minute, min_timestamp.second


@callback(
    Output('memory-corrected_rides', 'data', allow_duplicate=True),
    #Input('start_button', 'n_clicks'),
    Input('start_hour_input', 'value'),
    Input('start_minutes_input', 'value'),
    Input('start_seconds_input', 'value'),
    State('memory-rides', 'data'),
    prevent_initial_call=True
)
#def correct_rides(n_clicks, rides, hour, minute, seconds):
def correct_rides(hour, minute, seconds, rides):
    corrected_rides = {}

    if rides is not None and rides != {}:
        for rider, rider_data in rides.items():
            start_timestamp = datetime.fromisoformat(rider_data[0]['timestamp'])
            start_timestamp = start_timestamp.replace(hour=hour, minute=minute, second=seconds)
            #start_timestamp = (rider_data[0]['timestamp'].
            #                   replace(hour=int(hour), minute=int(minute), second=int(seconds)))
            corrected_data = []
            distance_offset = None
            for row in rider_data:
                if datetime.fromisoformat(row['timestamp']) >= start_timestamp:
                    if distance_offset is None:
                        distance_offset = row['distance']

                    # Correct the starting distance reference in the row
                    row['distance'] = row['distance'] - distance_offset
                    corrected_data.append(row)

            corrected_rides[rider] = corrected_data

    return corrected_rides


@callback(
    Output("download-table_xlsx", "data"),
    Input("download-table", "n_clicks"),
    State('memory-comparative_table', 'data'),
    prevent_initial_call=True,
)
def download(n_clicks, comparative_table):
    df = pd.DataFrame(comparative_table)

    return dcc.send_data_frame(df.to_excel, "comparative.xlsx", sheet_name="Sheet_name_1")


'''
# TODO: Remove the callback. The info of who is the leader is already in the value of the dropdown list, i.e., it is
# not neccessary to save anywhere else
@callback(
    Output('memory-leader', 'data', allow_duplicate=True),
    Input('leader', 'value'),
    prevent_initial_call=True
)
def select_leader(leader_value):
    memory = {'name' :  leader_value}

    return memory
'''


#######################

#######################
# Auxiliary
#######################
def build_htmlTable(df):
    component = html.Div([
        html.H2('Results'),
        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns],
            style_table={'overflowX': 'auto'}
        ),
    ]
    )

    return component


def parse_contents(content_files, filenames):
    data = {}
    suffix = '.fit.gz'
    for content, name in zip(content_files, filenames):
        if name.endswith(suffix):
            name = name[:-len(suffix)].lower()

        content_type, content_string = content.split(',')

        decoded = base64.b64decode(content_string)

        fit_raw_data = gzip.decompress(decoded)

        stream = Stream.from_byte_array(fit_raw_data)  # Stream.from_byte_array(io.BytesIO(decoded))
        decoder = Decoder(stream)
        messages, errors = decoder.read()

        if len(messages['record_mesgs']) > 3:
            data[name] = {
                'ride': messages['record_mesgs'],
                'events': messages['event_mesgs']
            }

    return data


def add_cs(df, period_list):
    # period_list in minutes,
    for period in period_list:
        if 'power' in df.columns:
            df[f'cs {period}'] = df['power'].rolling(period * 60).mean()
        else:
            df[f'cs {period}'] = 0

    return df


def build_metrics(riders_data, weight_ftp):
    data = []
    for rider, rider_data in riders_data.items():
        if rider not in weight_ftp.keys():
            ftp = 1
            weight = 1
        else:
            ftp = weight_ftp[rider]['ftp']
            weight = weight_ftp[rider]['weight']

        df = pd.DataFrame(rider_data)
        df.timestamp = pd.to_datetime(df.timestamp)

        # Build the best powers
        df = add_best_power_values(df, [30, 60, 600, 1200, 3600])
        df = add_cs(df, [1, 5, 12])

        NP = compute_avg_NP(df)

        df['above FTP'] = df['power'].apply(lambda x: 1 if x > ftp else 0)

        AP_FTP = (df['above FTP'].sum() / df.shape[0]) * 100

        # computing coasting
        df['w is 0'] = df['power'].apply(lambda x: 1 if x <= 30 else 0)

        coasting = (df['w is 0'].sum() / df.shape[0]) * 100

        duration = df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]

        hours = duration.seconds // 3600

        minutes = (duration.seconds - hours * 3600) // 60

        seconds = duration.seconds - hours * 3600 - minutes * 60

        duration_str = f'{hours}:{minutes:02d}:{seconds:02d}'

        row = {
            'name': rider,
            'time': duration_str,
            'Pos': None,
            'Coasting': coasting,
            'distance': df['distance'].iloc[-1] / 1000,
            'Avg Speed': df['speed'].mean(),
            'Avg Power': df['power'].mean(),
            'NP': NP,
            'IF': NP / ftp,
            'AP  FTP': AP_FTP,
            'Work (Kj)': df['power'].sum() * 0.001,
            'Power/kg': df['power'].mean() / weight,
            'NP/kg': NP / weight,
            'Kj/kg': df['power'].sum() * 0.001 / weight,
            'Pmax': None,
            'Best 30" ': df['Best 30"'].max(),
            "Best 1'  ": df['Best 60"'].max(),
            "Best 10' ": df['Best 600"'].max(),
            "Best 20' ": df['Best 1200"'].max(),
            "Best 60' ": df['Best 3600"'].max(),
            "CS 1' ": (df['cs 1'].max() ** 2) / weight,
            "CS 5' ": (df['cs 5'].max() ** 2) / weight,
            "CS 12' ": (df['cs 12'].max() ** 2) / weight,
            'Avg HR': df['heart_rate'].mean() if 'heart_rate' in df.columns else 0
        }

        for k, v in row.items():
            if k != 'name' and k != 'time' and v is not None:
                row[k] = round(v, 2)

        data.append(row)

    df2show = pd.DataFrame(data)

    return df2show


def add_kilojoules_per_hour(data):
    df = pd.DataFrame(data)
    df.timestamp = pd.to_datetime(df.timestamp)

    # Convert power in watts to kilojoules (1 watt-second = 0.001 kilojoules)
    df['kilojoules'] = df['power'] * 0.001

    # Calculate the rolling sum over the last 3600 seconds (1 hour), assuming the data is in 1-second intervals
    tmp_df = df[['timestamp', 'kilojoules']].copy()
    tmp_df = tmp_df.set_index('timestamp')
    tmp_df.index = pd.to_datetime(tmp_df.index)
    tmp_df = tmp_df.rolling(window=timedelta(hours=1), min_periods=1).sum()
    df['kilojoules_last_hour'] = tmp_df['kilojoules'].values

    return df


##########
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server

app.layout = html.Div(
    [
        create_layout(),
        #dcc.Store(id='store', data={})
        dcc.Store(id='memory-rides', data={}),
        dcc.Store(id='memory-corrected_rides', data={}),
        dcc.Store(id='memory-comparative_table', data={}),  #comparative_df
        dcc.Store(id='memory-riders-data', data={}),
    ]

)

if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
