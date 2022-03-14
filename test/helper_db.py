import ast
import os
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import String, Integer, Boolean
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

#books_authors_link = Table('books_authors_link', Base.metadata,
#                           Column('book', Integer, ForeignKey('books.id'), primary_key=True),
#                           Column('author', Integer, ForeignKey('authors.id'), primary_key=True)
#                           )

class Books_Authors_Link(Base):
    __tablename__ = 'books_authors_link'
    id = Column(Integer, primary_key=True, autoincrement=True)
    book = Column(Integer, primary_key=True)
    author = Column(Integer, primary_key=True)

    def __init__(self, book, author):
        self.book = book
        self.author = author


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

class Authors(Base):
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True)
    name = Column(String(collation='NOCASE'), unique=True, nullable=False)
    sort = Column(String(collation='NOCASE'))
    link = Column(String, nullable=False, default="")

    def __init__(self, name, sort):
        self.name = name
        self.sort = sort

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

class Data(Base):
    __tablename__ = 'data'

    id = Column(Integer, primary_key=True)
    book = Column(Integer, ForeignKey('books.id'), nullable=False)
    format = Column(String(collation='NOCASE'), nullable=False)
    uncompressed_size = Column(Integer, nullable=False)
    name = Column(String, nullable=False)

    def __init__(self, book, book_format, uncompressed_size, name):
        self.book = book
        self.format = book_format
        self.uncompressed_size = uncompressed_size
        self.name = name

    # ToDo: Check
    def get(self):
        return self.name

    def __repr__(self):
        return u"<Data('{0},{1}{2}{3}')>".format(self.book, self.format, self.uncompressed_size, self.name)


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


def _generate_random_cover(output_path):
    image = Image.new("RGB", (800, 1280), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    colors = ["red", "green", "blue", "yellow", "aquamarine", "darkgrey", "darkolivegreen", "rosybrown",
              "purple", "orange", "magenta", "black"]
    for i in range(0, 8):
        ele = [draw.ellipse, draw.line, draw.rectangle]
        random.choice(ele)((random.randint(0, 800), (random.randint(0, 1280))) + (random.randint(0, 800), (random.randint(0, 1280))), width=5, fill=random.choice(colors))
    image.save(output_path)


def add_books(location, number, cover=False):
    engine = create_engine('sqlite:///{0}'.format(location), echo=False)
    Session = scoped_session(sessionmaker())
    Session.configure(bind=engine)
    session = Session()

    Base.metadata.create_all(engine)
    database_root = location[:-len("metadata.db")]
    for i in range(number):
        update_title_sort(session)
        session.connection().connection.connection.create_function('uuid4', 0, lambda: str(uuid4()))
        book = Books()
        book.title = _randStr()
        book.sort = ""
        book.author_sort = _randStr()
        book.timestamp = datetime.utcnow()
        book.pubdate = datetime.utcnow()
        book.series_index = "1.0"
        book.last_modified = datetime.utcnow()
        book.path = ""
        book.uuid = str(uuid4())
        book.has_cover = int(cover)
        session.add(book)
        session.flush()
        os.makedirs(os.path.join(database_root, book.author_sort))
        book_folder = os.path.join(book.author_sort, book.title + " ({})".format(book.id))
        os.makedirs(os.path.join(database_root, book_folder))
        book.path = book_folder
        book_name = os.path.join(database_root, book_folder, "file.epub")
        with open(book_name, 'wb') as f_out:
            f_out.write(os.urandom(30))
        if cover:
            _generate_random_cover(os.path.join(database_root, book_folder, 'cover.jpg'))
        new_format = Data(name="file",
                          book_format="epub".upper(),
                          book=book.id, uncompressed_size=30)
        session.merge(new_format)
        author = Authors(book.author_sort, book.author_sort)
        session.add(author)
        session.flush()
        bal = Books_Authors_Link(book.id, author.id)
        session.add(bal)
        session.commit()
    # session.commit()
    session.close()
    engine.dispose()


