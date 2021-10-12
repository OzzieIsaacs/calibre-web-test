import ast
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import TIMESTAMP
import random
import string
from uuid import uuid4

try:
    # Compatibility with sqlalchemy 2.0
    from sqlalchemy.orm import declarative_base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Custom_Columns(Base):
    __tablename__ = 'custom_columns'

    id = Column(Integer, primary_key=True)
    label = Column(String)
    name = Column(String)
    datatype = Column(String)
    mark_for_delete = Column(Boolean)
    editable = Column(Boolean)
    display = Column(String)
    is_multiple = Column(Boolean)
    normalized = Column(Boolean)

    def get_display_dict(self):
        display_dict = ast.literal_eval(self.display)
        return display_dict

class Books(Base):
    __tablename__ = 'books'

    DEFAULT_PUBDATE = datetime(101, 1, 1, 0, 0, 0, 0)  # ("0101-01-01 00:00:00+00:00")

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(collation='NOCASE'), nullable=False, default='Unknown')
    sort = Column(String(collation='NOCASE'))
    author_sort = Column(String(collation='NOCASE'))
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    pubdate = Column(TIMESTAMP, default=DEFAULT_PUBDATE)
    series_index = Column(String, nullable=False, default="1.0")
    last_modified = Column(TIMESTAMP, default=datetime.utcnow)
    path = Column(String, default="", nullable=False)
    has_cover = Column(Integer, default=0)
    uuid = Column(String)
    isbn = Column(String(collation='NOCASE'), default="")
    flags = Column(Integer, nullable=False, default=1)


def update_title_sort(session):
    # user defined sort function for calibre databases (Series, etc.)
    def _title_sort(title):
        # calibre sort stuff
        return title.strip()

    conn = session.connection().connection.connection
    conn.create_function("title_sort", 1, _title_sort)

def _randStr(chars = string.ascii_uppercase + string.digits, N=10):
    return ''.join(random.choice(chars) for _ in range(N))


def delete_cust_class(location, id):
    engine = create_engine('sqlite:///{0}'.format(location), echo=False)
    Session = scoped_session(sessionmaker())
    Session.configure(bind=engine)
    session = Session()

    Base.metadata.create_all(engine)
    session.query(Custom_Columns).filter(Custom_Columns.id == id).delete()
    session.commit()
    session.close()
    engine.dispose()

def change_book_path(location, id):
    engine = create_engine('sqlite:///{0}'.format(location), echo=False)
    Session = scoped_session(sessionmaker())
    Session.configure(bind=engine)
    session = Session()

    Base.metadata.create_all(engine)
    update_title_sort(session)
    book = session.query(Books).filter(Books.id == id).first()
    book.path = "G/" + book.path
    session.commit()
    session.close()
    engine.dispose()

def add_books(location, number):
    engine = create_engine('sqlite:///{0}'.format(location), echo=False)
    Session = scoped_session(sessionmaker())
    Session.configure(bind=engine)
    session = Session()

    Base.metadata.create_all(engine)
    update_title_sort(session)
    session.connection().connection.connection.create_function('uuid4', 0, lambda: str(uuid4()))
    for i in range(number):
        book = Books()
        book.title = _randStr()
        book.sort = ""
        book.author_sort = _randStr()
        book.timestamp = datetime.utcnow()
        book.pubdate = datetime.utcnow()
        book.series_index = "1.0"
        book.last_modified = datetime.utcnow()
        book.path = ""
        book.has_cover = 0
        book.uuid = str(uuid4())
        #book.isbn = ""
        #book.flags = 1
        session.add(book)
    session.commit()
    session.close()
    engine.dispose()


