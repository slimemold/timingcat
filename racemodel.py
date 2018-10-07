import sys
from peewee import *

database_proxy = Proxy()

class BaseModel(Model):
    class Meta:
        database = database_proxy

class Race(BaseModel):
    name = CharField()

    # json/python dict for miscellaneous data (has no meaning for our model)..
    data = TextField()

class Field(BaseModel):
    name = CharField(unique=True)

    # json/python dict for miscellaneous data (has no meaning for our model)..
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

    start = TimeField
    finish = TimeField

    # json/python dict for miscellaneous data (has no meaning for our model)..
    data = TextField()

    @property
    def result(self):
        if not self.finish or not self.start:
            return None

        return self.finish - self.start

    @result.setter
    def result(self, result):
        self.finish = self.start + result

    def __repr__(self):
        return ('TimedRacer(bib=%r, name=%r, team=%r, start=%r, finish=%r)' %
                (self.bib, self.name, self.team, self.start, self.finish))

    def __str__(self):
        return ('%s, %s, %s, %s, %s, %s' %
                (self.bib, self.name, self.team, self.field.name,
                 self.start, self.finish))

class TempRacer(Racer):
    scratch_text = TextField()
    finish = TimeField

def create_racefile():
    with database_proxy:
        database_proxy.create_tables([Race, Field, Racer, TempRacer])

    database_proxy.connect()

    if Race.get_or_none() is None:
        with database_proxy.atomic():
            Race.create(name='(needs description)', data="{}")

