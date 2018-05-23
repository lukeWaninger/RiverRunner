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


repo = Repository()
runs = repo.get_all_runs_as_list()
options = [r.select_option for r in runs]

app = dash.Dash()
font_url = 'https://fonts.googleapis.com/css?family=Montserrat|Permanent+Marker'
app.css.append_css({
    'external_url': font_url
})


color_map = dict(
    unknown='#41434C',
    optimal='#4254CC',
    fair='#8F8A18',
    not_recommended='#A63617'
)


def color_scale(x):
    if x == -1.:
        return 'unknown'

    elif 0 <= x < .33:
        return 'optimal'

    elif .33 <= x < .66:
        return 'fair'

    elif .66 <= x < .99:
        return 'not_recommended'


def build_map():
    marker_sets = {'unknown': []}
    for run in runs:
        rating = color_scale(run.todays_runability)

        if rating not in marker_sets:
            marker_sets[rating] = []

        if rating is not None:
            marker_sets[rating].append(run)
        else:
            marker_sets['unknown'].append(run)

    def build_set(rating, ms):
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
                color=color_map[rating],
                opacity=0.8
            ),
            hoverinfo='text'
        )

    data = [build_set(key, value) for key, value in marker_sets.items() if key is not None]

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

    fig = dict(data=data, layout=layout)
    return fig


def build_timeseries(value):
    run = repo.get_run(value)
    if run.predictions is None:
        return None

    o_dates = [p.timestamp for p in run.observed_measurements]
    o_values = [p.fr for p in run.observed_measurements]

    p_dates = [p.timestamp for p in run.predicted_measurements]
    p_values = [p.fr for p in run.predicted_measurements]

    if len(p_dates) == 0:
        return go.Figure(data=[go.Scatter()], layout={'title': 'an error has occurred'})

    min_date = np.min(o_dates)
    max_date = np.max(p_dates)

    observed = go.Scatter(
        name='observed',
        x=o_dates,
        y=o_values,
        line=dict(
            color='#252E75',
            width=3
        )
    )

    predicted = go.Scatter(
        name='predicted',
        x=p_dates,
        y=p_values,
        line=dict(
            color='#C44200',
            width=3
        )
    )

    max_line = go.Scatter(
        x=[min_date, max_date],
        y=[run.max_level, run.max_level],
        showlegend=False,
        line=dict(
            color='#123B38',
            width=1,
            dash='dot')
    )

    min_line = go.Scatter(
        x=[min_date, max_date],
        y=[run.min_level, run.min_level],
        showlegend=False,
        line=dict(
            color='#123B38',
            width=1,
            dash='dot')
    )

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

    fig = go.Figure(data=[observed, predicted, max_line, min_line], layout=layout)
    return fig


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
    if not isinstance(value, int):
        return None

    fig = build_timeseries(value)
    return fig


@app.callback(Output('river_selection_container', 'children'), [
                  Input('river_map', 'clickData')
                ])
def update_dropdown(marker=None):
    if marker is not None:
        value = marker['points'][0]['id']

        return dcc.Dropdown(
                id='river_dropdown',
                options=options,
                value=value,
                multi=False
            )
    else:
        return dcc.Dropdown(
                id='river_dropdown',
                options=options,
                value=599,
                multi=False
            )


if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1')
