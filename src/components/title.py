from dash import html

def create_title():
    component = html.Div([
        html.H1([html.Span("Analytics"), html.Br(), html.Span("Dashboard")]),
        html.P("This dashboard prototype shows the initial functionality 1")
    ], style={"verticalAlignment": "top", "height": 260})
    return component
