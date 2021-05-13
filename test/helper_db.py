import sys
import ast

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import sessionmaker, scoped_session
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
        if sys.version_info < (3, 0):
            display_dict['enum_values'] = [x.decode('unicode_escape') for x in display_dict['enum_values']]
        return display_dict

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