from sqlalchemy import Column, Integer, String
from database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String)
    date = Column(String)
    price = Column(String)
    time = Column(String)
    website = Column(String)