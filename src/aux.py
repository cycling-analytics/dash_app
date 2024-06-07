from datetime import timedelta

import pandas as pd
from dash import  html,  dash_table
import base64
import gzip
from garmin_fit_sdk import Stream, Decoder

N_DECIMALS = 3


def parse_content(content):
    print("JF--> parse_content")
    data = None

    content_type, content_string = content.split(',')

    decoded = base64.b64decode(content_string)

    fit_raw_data = gzip.decompress(decoded)

    stream = Stream.from_byte_array(fit_raw_data)  # Stream.from_byte_array(io.BytesIO(decoded))
    decoder = Decoder(stream)
    messages, errors = decoder.read()

    if len(messages['record_mesgs']) > 3:
        data = {
            'ride': messages['record_mesgs'],
            'events': messages['event_mesgs']
        }

    print("JF<-- parse_content")
    return data


def add_best_power_values(df, period_list):
    # period_list in seconds, e.g, [30, 60, 600, 1200, 3600] for best 30", 1', 10', 20', 60'
    # Calculate the rolling sum over the last 3600 seconds (1 hour), assuming the data is in 1-second intervals
    for period in period_list:
        df[f'Best {period}"'] = df['power'].rolling(period).mean()

    return df


def compute_avg_NP(df):
    df_tmp = df.copy()
    df_tmp['rolling_average'] = df_tmp['power'].rolling(30).mean()
    df_tmp.dropna(subset=["rolling_average"], inplace=True)
    df_tmp.reset_index(drop=True, inplace=True)

    NP = df_tmp['rolling_average'].apply(lambda x: x ** 4)

    NP = NP.mean()

    return NP ** 0.25


def build_df_from_raw(content):
    data = parse_content(content)

    df = build_df(data['ride'], data['events'])

    return df


def build_df(record_msg, events_msg):
    # st.write('build_df')
    df = pd.DataFrame(record_msg)

    df['is_start'] = False

    # values without gps coordinates are uselss
    df.dropna(subset=["timestamp", "position_long", "position_lat", "distance", "enhanced_speed"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Transform into degrees
    df["position_long"] = (df["position_long"] / 11930465)
    df["position_lat"] = (df["position_lat"] / 11930465)

    df["rounded_long"] = df["position_long"].round(N_DECIMALS)
    df["rounded_lat"] = df["position_lat"].round(N_DECIMALS)

    # Transorm from m/s to Km/h
    df["speed"] = (df['enhanced_speed'] * 3.6).round(1)

    # Distance in meters
    df["distance"] = (df["distance"]).round().astype(int)

    start_hours = [msg['timestamp'].timestamp() for msg in events_msg if
                   (msg['event'] == 'timer' and msg['event_type'] == 'start')]

    df['is_start'] = df['timestamp'].apply(lambda x: x.timestamp() in start_hours)
    df.loc[0, 'is_start'] = True

    return df



def build_htmlTable(df):
    component = html.Div([
        html.H2('Results'),
        dash_table.DataTable(data=df.to_dict('records'), columns=[{'name': i, 'id': i} for i in df.columns],
                             style_table={'overflowX': 'auto'})
    ])
    return component


def add_cs(df, period_list):
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

        df = add_best_power_values(df, [30, 60, 600, 1200, 3600])
        df = add_cs(df, [1, 5, 12])
        NP = compute_avg_NP(df)
        df['above FTP'] = df['power'].apply(lambda x: 1 if x > ftp else 0)
        AP_FTP = (df['above FTP'].sum() / df.shape[0]) * 100
        df['w is 0'] = df['power'].apply(lambda x: 1 if x <= 30 else 0)
        coasting = (df['w is 0'].sum() / df.shape[0]) * 100
        duration = df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]
        hours = duration.seconds // 3600
        minutes = (duration.seconds - hours * 3600) // 60
        seconds = duration.seconds - hours * 3600 - minutes * 60
        duration_str = f'{hours}:{minutes:02d}:{seconds:02d}'
        row = {
            'name': rider, 'time': duration_str, 'Pos': None, 'Coasting': coasting,
            'distance': df['distance'].iloc[-1] / 1000,
            'Avg Speed': df['speed'].mean(), 'Avg Power': df['power'].mean(), 'NP': NP, 'IF': NP / ftp,
            'AP  FTP': AP_FTP,
            'Work (Kj)': df['power'].sum() * 0.001, 'Power/kg': df['power'].mean() / weight, 'NP/kg': NP / weight,
            'Kj/kg': df['power'].sum() * 0.001 / weight, 'Pmax': None, 'Best 30" ': df['Best 30"'].max(),
            "Best 1'  ": df['Best 60"'].max(), "Best 10' ": df['Best 600"'].max(), "Best 20' ": df['Best 1200"'].max(),
            "Best 60' ": df['Best 3600"'].max(), "CS 1' ": (df['cs 1'].max() ** 2) / weight,
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


def add_kilojoules_per_hour(df):
    df.timestamp = pd.to_datetime(df.timestamp)
    df['kilojoules'] = df['power'] * 0.001
    tmp_df = df[['timestamp', 'kilojoules']].copy()
    tmp_df = tmp_df.set_index('timestamp')
    tmp_df.index = pd.to_datetime(tmp_df.index)
    tmp_df = tmp_df.rolling(window=timedelta(hours=1), min_periods=1).sum()
    df['kilojoules_last_hour'] = tmp_df['kilojoules'].values
    return df


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