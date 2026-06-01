from dash import html, dcc, dash_table
from data_access import session
from models import Station, Pollutant, WeatherVariable
from dash import Output, Input, State
from dash import callback
from data_access import get_combined_measurements, get_aggregated_data
import pandas as pd
import plotly.express as px


stations = session.query(Station).all()
pollutants = session.query(Pollutant).all()
weather_vars = session.query(WeatherVariable).all()
@callback(
    Output('time-layout', 'style'),
    Output('quant-layout', 'style'),
    Output('spatial-layout', 'style'),
    Input('vis-type', 'value')
)
def toggle_layout(vis_type):
    return (
        {'display': 'block'} if vis_type == 'time' else {'display': 'none'},
        {'display': 'block'} if vis_type == 'quant' else {'display': 'none'},
        {'display': 'block'} if vis_type == 'spatial' else {'display': 'none'}
    )
@callback(
    [Output('graph-output', 'figure'), 
     Output('aggregation-output', 'children'),
     Output('data-table', 'columns'),
     Output('data-table', 'data')],
    Input('apply-button', 'n_clicks'),
    State('station-dropdown', 'value'),
    State('variable-dropdown', 'value'),
    State('date-picker', 'start_date'),
    State('date-picker', 'end_date'),
    State('vis-type', 'value'),
    State('aggregation-dropdown', 'value'),
    State('interval-dropdown', 'value'),
    State('min-value', 'value'),
    State('max-value', 'value'),
    State('sort-mode-dropdown', 'value'),
    State('sort-n-input', 'value'),
    State('spatial-agg-dropdown', 'value'),


)

def update_graph_callback(n_clicks, station_code, variable_names, start_date, end_date, vis_type,
                          agg_func, interval, min_value, max_value, sort_mode, sort_n, spatial_agg):
    return update_graph(n_clicks, station_code, variable_names, start_date, end_date,
                        vis_type, agg_func, interval, min_value, max_value, sort_mode, sort_n,spatial_agg)

def update_graph(n_clicks, station_code, variable_names, start_date, end_date, vis_type,
                 agg_func='max', interval='W', min_value=None, max_value=None,
                 sort_mode=None, sort_n=None, spatial_agg = 'mean'):
    if n_clicks == 0:
        return {"data": [], "layout": {"title": "Click 'Apply'"}}, "", [], []

    if not variable_names or not start_date or not end_date:
        return {"data": [], "layout": {"title": "Fill in all fields"}}, "", [], []

    date_start = pd.to_datetime(start_date)
    date_end = pd.to_datetime(end_date)

    if vis_type == "quant":
        if not agg_func or not interval:
            return {"data": [], "layout": {"title": "Select aggregation and interval"}}, "", [], []

        df = get_aggregated_data(
            session=session,
            station_code=station_code,
            variable_names=variable_names,
            date_start=date_start,
            date_end=date_end,
            interval=interval,
            agg_func=agg_func
        )

        if df.empty:
            return {"data": [], "layout": {"title": "Lack of data"}}, "", [], []

    # Sortowanie: top N lub bottom N
        if sort_mode in ['top', 'bottom'] and sort_n is not None:
            ascending = (sort_mode == 'bottom')
            df = df.sort_values(by='value', ascending=ascending).groupby('type').head(sort_n)

    # Konwersja daty do stringa dla czytelności tabeli
        df['date'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Wykres
        fig = px.bar(df, x='date', y='value', color='type',
                 title=f'{agg_func.capitalize()} values grouped by {interval}')

    # Tabela
        table_columns = [{"name": col, "id": col} for col in df.columns]
        table_data = df.to_dict('records')

        return fig, "", table_columns, table_data
    
    
    
    elif vis_type == "spatial":
        if not variable_names or not start_date or not end_date:
            return {"data": [], "layout": {"title": "Fill in the data"}}, "", [], []

    # Pomiary
        data = get_combined_measurements(
            session=session,
            variable_names=variable_names,
            date_start=start_date,
            date_end=end_date
        )

        if not data:
            return {"data": [], "layout": {"title": "No data"}}, "", [], []

        df = pd.DataFrame(data, columns=['value', 'date', 'type', 'station_id'])
        df['date'] = pd.to_datetime(df['date'])

    # Łączenie z lokalizacjami stacji
        stations_df = pd.DataFrame(
            [(s.id, s.name, s.code, s.latitude, s.longitude) for s in stations],
            columns=['station_id', 'station_name', 'station_code', 'lat', 'lon']
        )

        df = df.merge(stations_df, on='station_id')
        agg_func_map = {'min': 'min', 'max': 'max', 'mean': 'mean', 'sum': 'sum'}
        agg_func_name = agg_func_map.get(spatial_agg, 'mean')

        df_grouped = df.groupby(['station_id', 'station_name', 'lat', 'lon'])['value'].agg(agg_func_name).reset_index()

        fig = px.scatter_mapbox(df_grouped,
                            lat="lat", lon="lon",
                            color="value", size="value",
                            hover_name="station_name",
                            color_continuous_scale="YlOrRd",
                            mapbox_style="open-street-map",
                            size_max=15,
                            zoom=10,
                            height=600,
                            title=f"{agg_func_name} value '{variable_names}'")
        fig.update_layout(
        mapbox_center={"lat": 37.9838, "lon": 23.7275},  # Ateny
        mapbox_style="carto-positron",
        margin={"r":0,"t":40,"l":0,"b":0}
        )

        table_columns = [{"name": col, "id": col} for col in df_grouped.columns]
        table_data = df_grouped.to_dict('records')

        return fig, "", table_columns, table_data


    elif vis_type == "time":
        combined_data = get_combined_measurements(
            session=session,
            station_code=station_code,
            variable_names=variable_names,
            date_start=date_start,
            date_end=date_end,
            min_value=min_value,
            max_value=max_value
        )

        if not combined_data:
            return {"data": [], "layout": {"title": "No data"}}, "", [], []

        df = pd.DataFrame(combined_data, columns=['value', 'date', 'type', 'station_id'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        fig = px.line(df, x='date', y='value', color='station_id',
                      title='Time series chart')

    
    table_columns = [{"name": col, "id": col} for col in df.columns]
    table_data = df.to_dict('records')

    return fig, "", table_columns, table_data
layout = html.Div([
    dcc.RadioItems(
        id='vis-type',
        options=[
            {'label': 'Time Series', 'value': 'time'},
            {'label': 'Quantitative Analysis', 'value': 'quant'},
            {'label': 'Spatial Analysis', 'value': 'spatial'}
        ],
        value='time',
        labelStyle={'marginRight': '15px'}
    ),
    dcc.Dropdown(
        id='variable-dropdown',
        options=[
            {'label': v.name, 'value': v.name} for v in pollutants + weather_vars],
        placeholder="Select variable(s)",
        multi=True
    ),
    dcc.Dropdown(id='station-dropdown', options=[{'label': s.name, 'value': s.code} for s in stations], placeholder="Select station", multi = True),
    dcc.DatePickerRange(id='date-picker'),

    html.Div(id='time-layout', children=[
    html.Label("Minimum value:"),
    dcc.Input(id='min-value', type='number', placeholder='Min', debounce=True),
    html.Label("Maximum value:"),
    dcc.Input(id='max-value', type='number', placeholder='Max', debounce=True)], style={'margin': '10px 0'}),
    
    
    html.Div(id='quant-layout', children=[
        dcc.Dropdown(id='aggregation-dropdown', options=[
            {'label': 'Min', 'value': 'min'},
            {'label': 'Max', 'value': 'max'},
            {'label': 'Average', 'value': 'avg'},
            {'label': 'Sum', 'value': 'sum'}
        ], value = 'max', placeholder="Select aggregation"),
        dcc.Dropdown(id='interval-dropdown', options=[
            {'label': 'Hourly', 'value': 'H'},
            {'label': 'Daily', 'value': 'D'},
            {'label': 'Weekly', 'value': 'W'},
            {'label': 'Monthly', 'value': 'M'}
        ], value = 'W', placeholder="Select interval")
        , dcc.Dropdown(
        id='sort-mode-dropdown',
        options=[
            {'label': 'Top N (largest)', 'value': 'top'},
            {'label': 'Bottom N (smallest)', 'value': 'bottom'}
        ],
        placeholder="Select sort type"
    ),
    dcc.Input(
        id='sort-n-input',
        type='number',
        min=1,
        step=1,
        placeholder='Number of records N'
    )]),
        html.Button('Apply', id='apply-button', n_clicks=0),
        html.Div(id='aggregation-output'),
        dcc.Graph(id='graph-output'),
        dash_table.DataTable(
            id='data-table',
            columns=[], 
            data=[],
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
            style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'}
),
html.Div(id='spatial-layout', children=[dcc.Dropdown(id='spatial-agg-dropdown', options=[
        {'label': 'Min', 'value': 'min'},
        {'label': 'Max', 'value': 'max'},
        {'label': 'Average', 'value': 'mean'},
        {'label': 'Sum', 'value': 'sum'}
    ], value='mean', placeholder="Select aggregation")])
])