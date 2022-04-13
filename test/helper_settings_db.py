import ast
import os
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import String, Integer, Boolean, SmallInteger, DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import TIMESTAMP
import random
import string
from uuid import uuid4
from PIL import Image, ImageDraw

try:
    # Compatibility with sqlalchemy 2.0
    from sqlalchemy.orm import declarative_base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Thumbnail(Base):
    __tablename__ = 'thumbnail'

    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer)
    uuid = Column(String, unique=True)
    format = Column(String)
    type = Column(SmallInteger)
    resolution = Column(SmallInteger)
    filename = Column(String)
    generated_at = Column(DateTime)
    expiration = Column(DateTime, nullable=True)


def get_thumbnail_files(location, book_id):
    engine = create_engine('sqlite:///{0}'.format(location), echo=False)
    Session = scoped_session(sessionmaker())
    Session.configure(bind=engine)
    session = Session()

    Base.metadata.create_all(engine)
    book_entries = session.query(Thumbnail).filter(Thumbnail.entity_id == book_id).all()
    session.close()
    engine.dispose()
    return book_entries


