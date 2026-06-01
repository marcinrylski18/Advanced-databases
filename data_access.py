import pandas as pd
from sqlalchemy import and_
from database import session
from models import (
    Station, Pollutant, WeatherVariable, MeasurementDate,
    PollutionMeasurement, WeatherMeasurement
)

def get_combined_measurements(session, station_code=None, variable_names=None, date_start=None, date_end=None, min_value=None, max_value=None):
    date_start = pd.to_datetime(date_start) if date_start else pd.to_datetime('2020-05-01 00:00:00')
    date_end = pd.to_datetime(date_end) if date_end else pd.to_datetime('2023-05-29 23:00:00')
    pollution_data = []
    weather_data = []

    def flexible_filter(column, value):
        if value is None:
            return None
        if isinstance(value, (list, tuple, set)):
            return column.in_(value)
        return column == value

    if variable_names:
        pollution_filters = [
            flexible_filter(Station.code, station_code),
            Pollutant.name.in_(variable_names),
            MeasurementDate.timestamp >= date_start,
            MeasurementDate.timestamp <= date_end
        ]
        if min_value is not None:
            pollution_filters.append(PollutionMeasurement.value >= min_value)
        if max_value is not None:
            pollution_filters.append(PollutionMeasurement.value <= max_value)

        pollution_filters = [f for f in pollution_filters if f is not None]  # usuń None

        pollution_query = session.query(
            PollutionMeasurement.value.label('value'),
            MeasurementDate.timestamp.label('date'),
            Pollutant.name.label('type'),
            PollutionMeasurement.station_id.label('station_id')
        ).join(MeasurementDate, PollutionMeasurement.date_id == MeasurementDate.id)\
         .join(Station, PollutionMeasurement.station_id == Station.id)\
         .join(Pollutant, PollutionMeasurement.pollutant_id == Pollutant.id)\
         .filter(*pollution_filters)

        weather_filters = [
            flexible_filter(Station.code, station_code),
            WeatherVariable.name.in_(variable_names),
            MeasurementDate.timestamp >= date_start,
            MeasurementDate.timestamp <= date_end
        ]
        if min_value is not None:
            weather_filters.append(WeatherMeasurement.value >= min_value)
        if max_value is not None:
            weather_filters.append(WeatherMeasurement.value <= max_value)

        weather_filters = [f for f in weather_filters if f is not None]

        weather_query = session.query(
            WeatherMeasurement.value.label('value'),
            MeasurementDate.timestamp.label('date'),
            WeatherVariable.name.label('type'),
            WeatherMeasurement.station_id.label('station_id')
        ).join(MeasurementDate, WeatherMeasurement.date_id == MeasurementDate.id)\
         .join(Station, WeatherMeasurement.station_id == Station.id)\
         .join(WeatherVariable, WeatherMeasurement.variable_id == WeatherVariable.id)\
         .filter(*weather_filters)

        pollution_data = pollution_query.all()
        weather_data = weather_query.all()

    return pollution_data + weather_data

def get_aggregated_data(session, station_code, variable_names, date_start, date_end, interval, agg_func):
    raw_data = get_combined_measurements(session, station_code, variable_names, date_start, date_end)
    if not raw_data:
        return pd.DataFrame()

    df = pd.DataFrame(raw_data, columns=['value', 'date', 'type', 'station_id'])
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    agg_map = {'min': 'min', 'max': 'max', 'mean': 'mean', 'sum': 'sum'}
    agg_func_name = agg_map.get(agg_func, 'mean')

    df_grouped = df.groupby('type').resample(interval).agg({'value': agg_func_name}).reset_index()
    return df_grouped
