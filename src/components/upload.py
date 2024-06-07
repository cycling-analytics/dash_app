from dash import html, dcc


def create_upload():
    component = html.Div([
        html.H2('Race files'),
        dcc.Upload(
            id='upload-fit-data',
            children=html.Div(['Drag and Drop or ', html.A('Select fit.gz Files')]),
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
    """
    Upload the info of the rider as weight, FTP...
    :return:
    """
    component = html.Div([
        html.H2("Rider Info"),
        dcc.Upload(
            id='upload-riders-data',
            children=html.Div([html.A('Select file with riders info')]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px',
                'color': 'white'},
            # Don't allow multiple files to upload
            multiple=False)
    ])
    return component



