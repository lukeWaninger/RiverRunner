"""
Module for the user interface
"""

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import plotly.graph_objs as go
from riverrunner.repository import Repository
from riverrunner import settings

"""IP address for running application"""
HOST_IP = '192.168.80.13'

"""enable for application debugging features"""
DEBUG = False

"""mapping from river's predicted status to a color codes"""
COLOR_MAP = dict(
    unknown='#41434C',
    optimal='#4254CC',
    fair='#8F8A18',
    not_recommended='#A63617'
)

# create a new repository instance and retrieve all river runs
repo = Repository()
runs = repo.get_all_runs_as_list()
options = [r.select_option for r in runs]

# create a new Dash app adding custom fonts and css
app = dash.Dash()
font_url = 'https://fonts.googleapis.com/css?family=Montserrat|Permanent+Marker'
app.css.append_css({
    'external_url': font_url
})


def color_scale(x):
    """prediction binning

    method bins river predictions into discrete categories for color coding

    Args:
        x: (float) quantitative prediction rating

    Returns:
        str for associated bin
    """
    if x == -1.:
        return 'unknown'

    elif 0 <= x < .33:
        return 'optimal'

    elif .33 <= x < .66:
        return 'fair'

    elif .66 <= x < .99:
        return 'not_recommended'


def build_set(rating, ms):
    """build a set of markers

    Args:
        rating: (str) rating
        ms: [RiverRun] list of runs in bin

    Returns:
        plotly.graph_objs.Scattermapbox
    """
    return go.Scattermapbox(
        name=rating,
        lat=[run.put_in_latitude for run in ms],
        lon=[run.put_in_longitude for run in ms],
        text=[f'{run.run_name}</br></br>rating: {run.class_rating}</br>distance: {run.distance} mile(s)' for run in
              ms],
        ids=[run.run_id for run in ms],
        mode='markers',
        marker=dict(
            size=12,
            color=COLOR_MAP[rating],
            opacity=0.8
        ),
        hoverinfo='text'
    )


def build_map():
    """build the map figure

    map is built by referencing the runs retrieved at the current module level

    Returns:
        dict: {data=[graph_objs.Scattermapbox], layout=graph_ojbs.Layout}
    """
    # bin the map's markers by predicted flow rating
    marker_sets = {'unknown': []}
    for run in runs:
        rating = color_scale(run.todays_runability)

        if rating not in marker_sets:
            marker_sets[rating] = []

        if rating is not None:
            marker_sets[rating].append(run)
        else:
            marker_sets['unknown'].append(run)

    # build marker sets for each bin
    data = [build_set(key, value) for key, value in marker_sets.items() if key is not None]

    # create the map layout
    layout = go.Layout(
        autosize=True,
        height=550,
        hovermode='closest',
        mapbox=dict(
            accesstoken=settings.MAPBOX,
            bearing=0,
            center=dict(
                lat=47,
                lon=-122
            ),
            pitch=0,
            zoom=7
        ),
        margin=dict(l=10, r=10, b=0, t=0),
        legend=dict(
            traceorder='normal',
            orientation='h',
            x=0,
            y=-.01,
            font=dict(
                family='sans-serif',
                size=14,
                color='#000'
            ),
            bgcolor='#FFFFFF',
            bordercolor='#FFFFFF',
            borderwidth=2
        )
    )

    return dict(data=data, layout=layout)


def build_timeseries(value):
    """build the timeseries plot

    Args:
        value: (int) RiverRun.run_id

    Returns:
        graph_objs.Figure
    """
    run = repo.get_run(value)
    if run.predictions is None:
        return None

    # separate observed dates and values into lists
    o_dates  = [p.timestamp for p in run.observed_measurements]
    o_values = [p.fr for p in run.observed_measurements]

    # separate predicted dates and values into lists
    p_dates  = [p.timestamp for p in run.predicted_measurements]
    p_values = [p.fr for p in run.predicted_measurements]

    # if no predictions are found, return a Figure displaying an error message
    if len(p_dates) == 0:
        return go.Figure(data=[go.Scatter()], layout={'title': 'an error has occurred'})

    # get the min and max dates for x-axis
    min_date = np.min(o_dates)
    max_date = np.max(p_dates)

    # generate trace for observed measurements
    observed = go.Scatter(
        name='observed',
        x=o_dates,
        y=o_values,
        line=dict(
            color='#252E75',
            width=3
        )
    )

    # generate trace for predicted measurements
    predicted = go.Scatter(
        name='predicted',
        x=p_dates,
        y=p_values,
        line=dict(
            color='#C44200',
            width=3
        )
    )

    # generate line for maximum recommended flow rate
    max_line = go.Scatter(
        x=[min_date, max_date],
        y=[run.max_level, run.max_level],
        showlegend=False,
        line=dict(
            color='#123B38',
            width=1,
            dash='dot')
    )

    # generate line for minimum recommended flow rate
    min_line = go.Scatter(
        x=[min_date, max_date],
        y=[run.min_level, run.min_level],
        showlegend=False,
        line=dict(
            color='#123B38',
            width=1,
            dash='dot')
    )

    # create the layout building rectangle shapes for binned flow rate ratings
    layout = go.Layout(
        title="Flow Rate",
        yaxis={'title': 'Flow Rate'},
        shapes=[{
            'type': 'rect',
            'xref': 'x',
            'yref': 'y',
            'x0': min_date,
            'y0': run.min_level,
            'x1': max_date,
            'y1': run.max_level,
            'fillcolor': '#d3d3d3',
            'opacity': 0.2,
            'line': {
               'width': 0,
            }
        }],
        legend=dict(
            traceorder='normal',
            orientation='h',
            x=0,
            y=1.12,
            font=dict(
                family='sans-serif',
                size=14,
                color='#000'
            ),
            bgcolor='#FFFFFF',
            bordercolor='#FFFFFF',
            borderwidth=2
        )
    )

    return go.Figure(data=[observed, predicted, max_line, min_line], layout=layout)


# setup the main application layout
app.layout = html.Div([
    html.Div(
        id='navbar',
        children=[
            html.H1('River Runners',
                    id='heading',
                    style={'fontFamily': 'Permanent Marker'}
                    )
        ],
        style={
            'width': '100%',
            'textAlign': 'center',
            'marginTop': '-10px',
            'backgroundColor': '#3F4041',
            'color': '#BDC1C4'
        }),
    html.Div(
        id='river_selection_container',
        children=[
            dcc.Dropdown(
                id='river_dropdown',
                options=options,
                value=599,
                multi=False
            )
        ],
        style={
            'width': '80%',
            'padding': 10,
            'textAlign': 'center',
            'marginLeft': 'auto',
            'marginRight': 'auto',
            'marginTop': '-30px'
        }
    ),
    html.Div(
        id='ts_container',
        children=dcc.Graph(id='time_series',
                           figure=build_timeseries(599)),
    ),
    html.Div(id='map_container',
             children=dcc.Graph(
                 id='river_map',
                 figure=build_map(),
                 style={
                     'padding': '5px 20px 5px 20px',
                     'minHeight': '650px',
                     'marginTop': '-10px'
                }
             ))
    ],
    style={
        'font-family': ['Montserrat', 'sans-serif']
    }
)


@app.callback(Output('time_series', 'figure'), [
                  Input('river_dropdown', 'value'),
                  Input('river_map', 'clickData')
                ])
def update_timeseries(value=599, marker=None):
    """update the times series

    callback is triggered when either the drop-down changes values or a marker
    on the map is selected

    Args:
        value: (int) selected RiverRun run_id
        marker: (dict) graph_objs.Scattermapbox state
    """
    # make sure the request is valid
    if not isinstance(value, int):
        return None

    # return the plot
    return build_timeseries(value)


@app.callback(Output('river_selection_container', 'children'), [
                  Input('river_map', 'clickData')
                ])
def update_dropdown(marker=None):
    """update the drop-down selected value

    callback is triggered when a run is selected from the map. The drop-down is
    updated to match the selected run

    Args:
        marker: (dict) graph_objs.Scattermapbox state
    """
    # make sure the incoming value is valid
    if marker is not None:
        value = marker['points'][0]['id']

        return dcc.Dropdown(
                id='river_dropdown',
                options=options,
                value=value,
                multi=False
            )

    # else return the drop-down's default value
    else:
        return dcc.Dropdown(
                id='river_dropdown',
                options=options,
                value=599,
                multi=False
            )


def run_ui():
    app.run_server()
    return True


if __name__ == '__main__':
    app.run_server(debug=DEBUG, host=HOST_IP)
