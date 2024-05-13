import pandas as pd

N_DECIMALS = 3


def add_best_power_values(df, period_list):
    # period_list in seconds, e.g, [30, 60, 600, 1200, 3600] for best 30", 1', 10', 20', 60'
    # Calculate the rolling sum over the last 3600 seconds (1 hour), assuming the data is in 1-second intervals
    for period in period_list:
        df[f'Best {period}"'] = df['power'].rolling(period).mean()

    return df

def compute_avg_NP(df):
    df_tmp = df.copy()
    df_tmp['rolling_average']  = df_tmp['power'].rolling(30).mean()
    df_tmp.dropna(subset=["rolling_average"], inplace=True)
    df_tmp.reset_index(drop=True, inplace=True)

    NP = df_tmp['rolling_average'].apply(lambda x : x**4)

    NP = NP.mean()

    return NP**0.25

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