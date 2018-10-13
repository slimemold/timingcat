import logging
import sys
from peewee import *

logger = logging.getLogger(__name__)

database_proxy = Proxy()

class BaseModel(Model):
    class Meta:
        database = database_proxy

class Race(BaseModel):
    name = CharField()

    # JSON for miscellaneous data (has no meaning for our model)..
    data = TextField()

class Field(BaseModel):
    name = CharField(unique=True)

    # JSON for miscellaneous data (has no meaning for our model)..
    data = TextField()

class Racer(BaseModel):
    bib = IntegerField(unique=True)
    name = CharField()
    team = CharField()

    field = ForeignKeyField(Field, backref='racers')

    start = TimeField()
    finish = TimeField()

    # JSON for miscellaneous data (has no meaning for our model)..
    data = TextField()

class Result(BaseModel):
    finish = TimeField()

    # This ends up being used as a bib (way to identify the racer), but until
    # it is applied to a racer, it can be anything (hence, it's a scratchpad).
    scratchpad = TextField()

    # JSON for miscellaneous data (has no meaning for our model)..
    data = TextField()

def create_tables():
    with database_proxy:
        database_proxy.create_tables([Race, Field, Racer, Result])
