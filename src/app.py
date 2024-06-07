from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from layout import create_layout
import callbacks  # This imports and registers all callbacks
from components.memory import create_memory, MemoryRides

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server

app.layout = html.Div([
    create_layout(),
    create_memory()])



if __name__ == "__main__":
    app.run_server(debug=True)
