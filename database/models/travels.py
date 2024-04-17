from sqlalchemy import Integer, String, Date, Column, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship

from ..core import Base


class Location(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date_start = Column(Date)
    date_end = Column(Date)
    timezone = Column(String, default="UTC+3")
    travel = Column(ForeignKey("travels.id"))
    user = Column(ForeignKey("users.id"))
    place = Column(String)
    lat = Column(Float)
    lon = Column(Float)


class TravelMember(Base):
    __tablename__ = 'travel_members'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey("users.id"))
    travel_id = Column(ForeignKey("travels.id"))


class TravelNote(Base):
    __tablename__ = 'travel_notes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    travel_id = Column(ForeignKey("travels.id"))
    created = Column(DateTime)
    content = Column(String)
    note_type = Column(String, default="text", server_default="text")
    file_url = Column(String)
    user_id = Column(ForeignKey("users.id"))
    name = Column(String)


class Travel(Base):
    __tablename__ = 'travels'
    id = Column(Integer, primary_key=True, autoincrement=True)
    _name = Column(String)
    _description = Column(String)
    user = Column(ForeignKey("users.id"))

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not 0 < len(value) < 31:
            raise ValueError("travel name error")
        self._name = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        if not 0 < len(value) < 256:
            raise ValueError("travel description error")
        self._description = value
