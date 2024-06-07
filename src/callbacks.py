from dash import callback, Output, Input, State
import dash_leaflet as dl

import base64
import yaml
import pandas as pd
from datetime import datetime
from layout import create_layout
from aux import build_htmlTable, build_metrics, add_kilojoules_per_hour, parse_contents, build_df
import uuid
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from components.memory import MemoryRides

rides_memory = MemoryRides()


#################
# Load data from files
################
@callback(Output('leader-dropdown', 'options'),
          Output('memory-rides-key', 'data'),
          Input('upload-fit-data', 'contents'),
          State('upload-fit-data', 'filename'),
          prevent_initial_call=True)
def update_data(list_of_contents, list_of_names):
    global rides_memory

    mem_key = ''

    if list_of_contents is not None:
        mem_key = str(uuid.uuid4())
        data = parse_contents(list_of_contents, list_of_names)

        rides = {}
        for name, info in data.items():
            rides[name] = build_df(info['ride'], info['events'])

        list_of_names = list(rides.keys())

        rides_memory.set_rides(mem_key, rides)

    return list_of_names, mem_key


@callback(
    Output('memory-riders-data', 'data', allow_duplicate=True),
    Input('upload-riders-data', 'contents'),
    State('upload-riders-data', 'filename'),
    prevent_initial_call=True
)
def update_riders_data(content, name):
    riders_dict = {}
    if content is not None:
        content_type, content_string = content.split(',')
        decoded = base64.b64decode(content_string)

        # Assuming the uploaded file is YAML
        riders_dict = yaml.safe_load(decoded)

    return riders_dict


##########################
# CORRECTING STARTING HOUR


@callback(
    Output('start_hour_input', 'value'),
    Output('start_minutes_input', 'value'),
    Output('start_seconds_input', 'value'),
    Input('memory-rides-key', 'data'),
    prevent_initial_call=True
)
def update_start_time_div(rides_key):
    global rides_memory

    rides = rides_memory.get_rides(rides_key)
    #start_time_seconds = 0
    #end_time_seconds = 0
    #marks = {}
    min_timestamp = datetime.now().timestamp()
    if rides is not None and rides != {}:
        min_times = []
        for rider, rider_df in rides.items():
            i = 0
            while rider_df.iloc[i]['timestamp'] is None:
                i += 1

            min_times.append(rider_df.iloc[i]['timestamp'])

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
    Output('map', 'children'),
    Output('map', 'center'),
    Input('start_hour_input', 'value'),
    Input('start_minutes_input', 'value'),
    Input('start_seconds_input', 'value'),
    State('memory-rides-key', 'data'),
    prevent_initial_call=True
)
#def correct_rides(n_clicks, rides, hour, minute, seconds):
def correct_rides(hour, minute, seconds, rides_key):
    global rides_memory

    rides = rides_memory.get_rides(rides_key)

    corrected_rides = {}

    if rides is not None and rides != {}:

        for name, df in rides.items():
            start_timestamp = df.iloc[0]['timestamp']
            start_timestamp = start_timestamp.replace(hour=hour, minute=minute, second=seconds)
            df['valid'] = df['timestamp'].apply(lambda x: x.timestamp() >= start_timestamp.timestamp())

            df_valid = df[df['valid']].reset_index().copy()

            # Correct the starting distance reference
            offset = df_valid.iloc[0]['distance']
            df_valid['distance'] = df_valid['distance'].apply(lambda x: x - offset)

            corrected_rides[name] = df_valid

        rides_memory.set_corrected_rides(rides_key, corrected_rides)

        return update_map(corrected_rides)


def update_map(rides):
    children = []
    center = (0, 0)
    if (rides is not None) and (len(rides) > 0):
        #       rides_corrected = {name: pd.DataFrame(data) for name, data in rides.items()}
        mean_starting_lat = sum([df["position_lat"].iloc[0] for _, df in rides.items()])
        mean_starting_lat /= len(rides)

        mean_starting_long = sum([df["position_long"].iloc[0] for _, df in rides.items()])
        mean_starting_long /= len(rides)

        center = (mean_starting_lat, mean_starting_long)

        marker_coords = [
            (df["position_lat"].iloc[0], df["position_long"].iloc[0])
            for _, df in rides.items()
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


### updating dashboard
@callback(
    Output('output_table', 'children'),
    Output('memory-comparative_table', 'data', allow_duplicate=True),
    Input('process-button', 'n_clicks'),
    State('memory-riders-data', 'data'),
    State('memory-rides-key', 'data'),
    prevent_initial_call=True,
)
def update_comparative_table(n_clicks, riders_data, rides_key):
    global rides_memory
    rides = rides_memory.get_corrected_rides(rides_key)

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
    Input('process-button', 'n_clicks'),
    State('memory-rides-key', 'data'),
    State('leader-dropdown', 'value'),
    prevent_initial_call=True,
)
def update_leader_comparative(n_clicks, rides_key, leader):
    global rides_memory
    rides = rides_memory.get_corrected_rides(rides_key)

    fig = make_subplots(specs=[[{"secondary_y": True}]])  #go.Figure()
    style = {'display': 'none'}

    if (rides is not None ) and (leader is not None ):
        style = {'display': 'flex'}
        # Initialize an empty DataFrame to store the differences
        #differences_df = pd.DataFrame()

        reference_df = rides[leader]
        reference_df.timestamp = pd.to_datetime(reference_df.timestamp)

        #Add activity profile to the graph

        fig.add_trace(
            go.Scatter(x=reference_df.distance / 1000, y=reference_df.altitude, mode='lines', name='altitude'),
            secondary_y=True
        )

        for rider, df in rides.items():
            if rider != leader:
                df.timestamp = pd.to_datetime(df.timestamp)

                max_length = min(df.shape[0], reference_df.shape[0])

                differences = (
                        df.iloc[:max_length]['distance'].values - reference_df.iloc[:max_length]['distance'].values
                )

                fig.add_trace(
                    go.Scatter(x=reference_df.distance / 1000, y=differences, mode='lines', name=rider),
                    secondary_y=False
                )

        fig.update_layout(
            title_text=f"<b>Distance with respect to the Leader {leader}</b>"
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
    Input('process-button', 'n_clicks'),
    State('memory-rides-key', 'data'),
    prevent_initial_call=True,
)
def update_speed_comparison(n_clicks, rides_key):
    global rides_memory
    rides = rides_memory.get_corrected_rides(rides_key)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    style = {'display': 'none'}

    if (rides is not None) :
        style = {'display': 'flex'}

        profile_plotted = False
        for rider, df in rides.items():
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
    Input('process-button', 'n_clicks'),
    State('memory-rides-key', 'data'),
    prevent_initial_call=True
)
def update_kilojoules_per_hour(n_clicks, rides_key):
    global rides_memory
    rides = rides_memory.get_corrected_rides(rides_key)

    fig = make_subplots(specs=[[{"secondary_y": True}]])  # go.Figure()
    style = {'display': 'none'}
    if rides is not None :
        style = {'display': 'flex'}

        profile_plotted = False
        dfs_with_kJ = {}
        for rider, df in rides.items():
            df = add_kilojoules_per_hour(df)

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

