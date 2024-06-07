from dash import html, dcc

class MemoryRides:
    def __init__(self):
        self.rides = {}
        self.corrected_rides  = {}
        self.rides_key = None
        self.corrected_rides_key = None

    def set_rides(self, key, ride_df):
        self.rides_key = key
        self.rides[key] = ride_df

    def set_corrected_rides(self, key, ride_df):
        self.corrected_rides_key = key
        self.corrected_rides[key] = ride_df

    def get_rides(self, key):
        if key != self.rides_key:
            raise KeyError(f"Rides data not consistent, please clear cache and load again the rides")

        return self.rides[key]

    def get_corrected_rides(self, key):
        if key != self.corrected_rides_key:
            raise KeyError(f"Rides data not consistent, please clear cache and load again the rides")

        return self.corrected_rides[key]

    def clear_history(self):
        self.rides = {}
        self.corrected_rides = {}
        self.rides_key = None
        self.corrected_rides_key = None



def create_memory():
    return html.Div([
        dcc.Store(id='memory-comparative_table', data={}),  # comparative_df
        dcc.Store(id='memory-riders-data', data={}),
        dcc.Store(id='memory-rides-key', data=''),
        dcc.Store(id='starting-hour', data={'hour': 0, 'minute': 0}),
    ])