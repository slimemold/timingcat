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

# A racer in a time trial. Has a start and finish time. The result is redefined
# to be a timedelta, and setting of start, finish, and result are maintained to
# be consistent.
#
# To set a racer's start time to today at 9:30am:
#   racer.start = datetime.datetime.now().replace(hours=9, minutes=30, seconds=0, microseconds=0)
#
# To set a racer's finish time to right now:
#   racer.finish = datetime.datetime.now()
#
# To set a racer's result time to 19 minutes:
#   racer.result = datetime.timedelta(minutes=19)
class Racer(BaseModel):
    bib = IntegerField(unique=True)
    name = CharField()
    team = CharField()

    field = ForeignKeyField(Field, backref='racers')

    start = TimeField()
    finish = TimeField()

    # JSON for miscellaneous data (has no meaning for our model)..
    data = TextField()

    @property
    def result(self):
        if not self.finish or not self.start:
            return None

        return self.finish - self.start

    @result.setter
    def result(self, result):
        self.finish = self.start + result

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
