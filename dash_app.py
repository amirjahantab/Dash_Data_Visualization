import dash
from dash import dcc, html, Input, Output, State
import dash_table
import pandas as pd
import plotly.express as px
import base64
import io

app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Designing the User Interface (Layout)
app.layout = html.Div([
    html.H1("CSV Data Visualization Tool"),
    
    # File Upload
    dcc.Upload(
        id='upload-data',
        children=html.Button("Upload CSV"),
        multiple=False
    ),

    html.H3(id='table-header'),

    # Data Table Preview (Only Head)
    dash_table.DataTable(id='data-table'),
    
    # X and Y Axis Selection
    html.Label("Select X-Axis"),
    dcc.Dropdown(id='x-axis-selector'),
    html.Label("Select Y-Axis"),
    dcc.Dropdown(id='y-axis-selector', multi=True),
    
    # Chart Type Selection
    html.Label("Select Chart Type"),
    dcc.Dropdown(
        id='chart-type',
        options=[ # available choices in the dropdown
            {'label': 'Scatter Plot', 'value': 'scatter'},
            {'label': 'Line Chart', 'value': 'line'},
            {'label': 'Bar Chart', 'value': 'bar'},
            {'label': 'Histogram', 'value': 'histogram'},
            {'label': 'Box Plot', 'value': 'box'},
            {'label': 'Violin Plot', 'value': 'violin'},
            {'label': 'Heatmap', 'value': 'heatmap'},
            {'label': 'Sunburst', 'value': 'sunburst'},
        ],
        value='scatter' # default value
    ),

    html.Div(id='bins-container'),

    html.Label("Select Color"),
    dcc.Dropdown(id='color-selector'),
    
    # Plot Button
    html.Button("Generate Chart", id='plot-button', n_clicks=0),
    
    # Graph Output
    dcc.Graph(id='output-graph')
])

# File Processing Callback
def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    return df


@app.callback(
    [Output('data-table', 'data'), # Updates the data in the preview table
     Output('x-axis-selector', 'options'), # Updates X-axis dropdown options
     Output('y-axis-selector', 'options'), # Updates Y-axis dropdown options
     Output('color-selector', 'options'),  # Updates Color selection dropdown
     Output('table-header', 'children'), # Updates table title
     ],
    Input('upload-data', 'contents') # Triggers this function when a CSV file is uploaded
)
def update_table(contents):
    if not contents:
        return [], [], [], [], ''
    df = parse_contents(contents)
    df_preview = df.head(5)  # Show head
    options = [{'label': col, 'value': col} for col in df.columns]
    return df_preview.to_dict('records'), options, options, options, "Data Table Preview (First 5 rows)"


@app.callback(
    Output('bins-container', 'children'),
    Input('chart-type', 'value'),
)
def display_bins_input(chart_type):
    if chart_type == 'histogram':
        return html.Div([
            html.Label('Number of Bins:'),
            dcc.Input(id='bins-number', type='number', value=10),
        ])
    else:
        return html.Div()


# Chart Generation Callback
@app.callback(
    Output('output-graph', 'figure'),
    Input('plot-button', 'n_clicks'),
    State('upload-data', 'contents'),
    State('x-axis-selector', 'value'),
    State('y-axis-selector', 'value'),
    State('color-selector', 'value'),
    State('chart-type', 'value'),
    State('bins-container', 'children'),  # Use the children of bins-container to check if bins-number exists
)
def generate_chart(n_clicks, contents, x_column, y_columns, color, chart_type, bins_container):
    if not contents or not x_column:
        return px.scatter()
    
    df = parse_contents(contents)

    # Extract bins-number safely
    bins = None
    if chart_type == 'histogram' and isinstance(bins_container, dict) and 'props' in bins_container:
        children = bins_container.get('props', {}).get('children', [])
        if isinstance(children, dict):  # Single component case
            children = [children]
        for component in children:
            if isinstance(component, dict) and component.get('props', {}).get('id') == 'bins-number':
                bins = component['props'].get('value', 10)

    if chart_type == 'histogram':
        fig = px.histogram(df, x=x_column, color=color, nbins=int(bins) if bins else 10)
    elif chart_type == 'scatter' and len(y_columns) >= 1:
        fig = px.scatter(df, x=x_column, y=y_columns)
    elif chart_type == 'line' and len(y_columns) >= 1:
        fig = px.line(df, x=x_column, y=y_columns)
    elif chart_type == 'bar' and len(y_columns) >= 1:
        fig = px.bar(df, x=x_column, y=y_columns, opacity=1.0)
    elif chart_type == 'box' and len(y_columns) >= 1:
        fig = px.box(df, x=x_column, y=y_columns)
    elif chart_type == 'violin' and len(y_columns) >= 1:
        fig = px.violin(df, x=x_column, y=y_columns)
    elif chart_type == 'heatmap' and len(y_columns) >= 1:
        fig = px.density_heatmap(df, x=x_column, y=y_columns)
    elif chart_type == 'sunburst' and len(y_columns) >= 1:
        y_columns = y_columns[0]  # Select the first categorical column
        fig = px.sunburst(df, path=[x_column, y_columns])  # Use categorical columns
    else:
        fig = px.scatter()
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)