import os
import raceops
import unittest

class TestBase(unittest.TestCase):
    RACE_FILE='sbhc2018.rce'
    RACE_KEY='Race name'
    RACE_VALUE='San Bruno Hillclimb 2018'

    def open_race_file():
        raceops.race_init(TestBase.RACE_FILE)

    def close_race_file():
        raceops.race_cleanup()

    def delete_race_file():
        try:
            os.remove(TestBase.RACE_FILE)
        except OSError:
            pass
