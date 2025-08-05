import ast
import os
from datetime import datetime, UTC
import random
import shutil
import string
from uuid import uuid4
from PIL import Image, ImageDraw

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import String, Integer, Boolean
from sqlalchemy import ForeignKey
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import TIMESTAMP

from config_test import base_path

try:
    # Compatibility with sqlalchemy 2.0
    from sqlalchemy.orm import declarative_base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class LibraryId(Base):
    __tablename__ = 'library_id'
    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False)


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

class Tags(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(collation='NOCASE'), unique=True, nullable=False)

    def __init__(self, name):
        super().__init__()
        self.name = name

class Books(Base):
    __tablename__ = 'books'

    DEFAULT_PUBDATE = datetime(101, 1, 1, 0, 0, 0, 0)  # ("0101-01-01 00:00:00+00:00")

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(collation='NOCASE'), nullable=False, default='Unknown')
    sort = Column(String(collation='NOCASE'))
    author_sort = Column(String(collation='NOCASE'))
    timestamp = Column(TIMESTAMP, default=datetime.now(UTC))
    pubdate = Column(TIMESTAMP, default=DEFAULT_PUBDATE)
    series_index = Column(String, nullable=False, default="1.0")
    last_modified = Column(TIMESTAMP, default=datetime.now(UTC))
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
    try:
        # sqlalchemy <1.4.24 or > sqlalchemy 2.0
        conn = session.connection().connection.driver_connection
    except AttributeError:
        # sqlalchemy >1.4.24 and sqlalchemy 2.0
        conn = session.connection().connection.connection
    try:
        conn.create_function("title_sort", 1, _title_sort)
    except Exception:
        pass

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

def change_tag(location, old_name, new_name):
    engine = create_engine('sqlite:///{0}'.format(location), echo=False)
    Session = scoped_session(sessionmaker())
    Session.configure(bind=engine)
    session = Session()

    Base.metadata.create_all(engine)
    tag = session.query(Tags).filter(Tags.name == old_name).first()
    tag.name = new_name
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
        x0 = random.randint(0, 799)
        y0 = random.randint(0, 1279)
        x1 = random.randint(x0, 800)
        y1 = random.randint(y0, 1280)
        random.choice(ele)((x0, y0) + (x1, y1), width=5, fill=random.choice(colors))
    image.save(output_path)


def add_books(location, number, cover=False, set_id=False, no_data=False):
    engine = create_engine('sqlite:///{0}'.format(location), echo=False)
    Session = scoped_session(sessionmaker())
    Session.configure(bind=engine)
    session = Session()

    Base.metadata.create_all(engine)
    if set_id:
        database_uuid = session.query(LibraryId).one_or_none()
        database_uuid.uuid = str(uuid4())
        session.commit()
    database_root = location[:-len("metadata.db")]
    for i in range(number):
        update_title_sort(session)
        try:
            # sqlalchemy <1.4.24
            conn = session.connection().connection.driver_connection
        except AttributeError:
            # sqlalchemy >1.4.24 and sqlalchemy 2.0
            conn = session.connection().connection.connection
        conn.create_function('uuid4', 0, lambda: str(uuid4()))
        book = Books()
        book.title = _randStr()
        book.sort = ""
        book.author_sort = _randStr()
        book.timestamp = datetime.now(UTC)
        book.pubdate = datetime.now(UTC)
        book.series_index = "1.0"
        book.last_modified = datetime.now(UTC)
        book.path = ""
        book.uuid = str(uuid4())
        book.has_cover = int(cover)
        session.add(book)
        session.flush()
        os.makedirs(os.path.join(database_root, book.author_sort))
        book_folder = os.path.join(book.author_sort, book.title + " ({})".format(book.id))
        os.makedirs(os.path.join(database_root, book_folder))
        book.path = book_folder
        if not no_data:
            # copy real book info
            epub_file = os.path.join(base_path, 'files', 'book.epub')
            shutil.copy(epub_file, os.path.join(database_root, book_folder, "file.epub"))
            new_format = Data(name="file",
                              book_format="epub".upper(),
                              book=book.id, uncompressed_size=30)
            session.merge(new_format)
        if cover:
            _generate_random_cover(os.path.join(database_root, book_folder, 'cover.jpg'))

        author = Authors(book.author_sort, book.author_sort)
        session.add(author)
        session.flush()
        bal = Books_Authors_Link(book.id, author.id)
        session.add(bal)
        session.commit()
    session.close()
    engine.dispose()

def remove_book(location, book_id):
    engine = create_engine('sqlite:///{0}'.format(location), echo=False)
    Session = scoped_session(sessionmaker())
    Session.configure(bind=engine)
    session = Session()
    del_book = session.query(Books).filter(Books.id == book_id).first()
    # delete path
    database_root = location[:-len("metadata.db")]
    shutil.rmtree(os.path.join(database_root, del_book.path))
    session.query(Data).filter(Data.book == book_id).delete()
    session.query(Books).filter(Books.id == book_id).delete()
    session.commit()
    Base.metadata.create_all(engine)
    session.close()
    engine.dispose()

def change_book_cover(location, book_id, cover_path):
    engine = create_engine('sqlite:///{0}'.format(location), echo=False)
    Session = scoped_session(sessionmaker())
    Session.configure(bind=engine)
    session = Session()
    update_title_sort(session)
    # file_location = session.query(Data).filter(Data.book == book_id).first()
    book = session.query(Books).filter(Books.id == book_id).first()
    database_root = location[:-len("metadata.db")]
    shutil.copy(cover_path, os.path.join(database_root, book.path, "cover.jpg"))
    book = session.query(Books).filter(Books.id == book_id).first()
    book.last_modified = datetime.now(UTC)
    session.commit()
    Base.metadata.create_all(engine)
    session.close()
    engine.dispose()
