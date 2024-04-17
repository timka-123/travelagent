from sqlalchemy import Column, BigInteger, String, DateTime, Integer

from ..core import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True)
    name = Column(String)
    age = Column(Integer, nullable=False)
    city = Column(String)
    country = Column(String)
    _bio = Column(String)

    @property
    def bio(self):
        return self._bio

    @bio.setter
    def bio(self, value):
        if not 0 < len(value) < 71:
            raise ValueError("bio length error")
        self._bio = value
    