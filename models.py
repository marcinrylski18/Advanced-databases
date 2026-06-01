from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Station(Base):
    __tablename__ = 'station'
    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)


class Pollutant(Base):
    __tablename__ = 'pollutant'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)  
    unit = Column(String, nullable=False)               

class WeatherVariable(Base):
    __tablename__ = 'weather_variable'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)   
    unit = Column(String)               

class MeasurementDate(Base):
    __tablename__ = 'measurement_date'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, unique=True, nullable=False)

class PollutionMeasurement(Base):
    __tablename__ = 'pollution_measurement'
    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey('station.id'), nullable=False)
    pollutant_id = Column(Integer, ForeignKey('pollutant.id'), nullable=False)
    date_id = Column(Integer, ForeignKey('measurement_date.id'), nullable=False)
    value = Column(Float)

class WeatherMeasurement(Base):
    __tablename__ = 'weather_measurement'
    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey('station.id'), nullable=False)
    variable_id = Column(Integer, ForeignKey('weather_variable.id'), nullable=False)
    date_id = Column(Integer, ForeignKey('measurement_date.id'), nullable=False)
    value = Column(Float)