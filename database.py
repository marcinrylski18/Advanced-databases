from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

db_string = "postgresql+psycopg2://postgres:admin@localhost:54320/air_pollution"
engine = create_engine(db_string)

Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()