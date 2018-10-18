import logging
import sys
from peewee import *

logger = logging.getLogger(__name__)

database_proxy = Proxy()

class BaseModel(Model):
    class Meta:
        database = database_proxy

class Race(BaseModel):
    key = TextField(primary_key=True)
    value = TextField()

class Field(BaseModel):
    name = TextField(unique=True)

    # JSON for miscellaneous data (has no meaning for our model)..
    data = TextField()

class Racer(BaseModel):
    bib = IntegerField(unique=True)
    name = TextField()
    team = TextField()

    field = ForeignKeyField(Field, backref='racers')

    start = TimeField()
    finish = TimeField()

    # JSON for miscellaneous data (has no meaning for our model)..
    data = TextField()

class Result(BaseModel):
    # This ends up being used as a bib (way to identify the racer), but until
    # it is applied to a racer, it can be anything (hence, it's a scratchpad).
    scratchpad = TextField()

    finish = TimeField()

    # JSON for miscellaneous data (has no meaning for our model)..
    data = TextField()

def create_tables():
    with database_proxy:
        database_proxy.create_tables([Race, Field, Racer, Result])
