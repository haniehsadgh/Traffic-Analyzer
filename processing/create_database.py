"""
Module to create and drop database tables.
"""

from models import Base
from db import engine

def create_tables():
    """
    Create all tables defined in the Base metadata.
    """
    Base.metadata.create_all(engine)


def drop_tables():
    """
    Drop all tables defined in the Base metadata.
    """
    Base.metadata.drop_all(engine)


if __name__ == "__main__":
    create_tables()
