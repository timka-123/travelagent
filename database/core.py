from os import environ

from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine


engine = create_engine(environ.get("POSTGRES_CONN"))
Base = declarative_base()
