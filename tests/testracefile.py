import raceops
import unittest
from tests.testbase import TestBase

class TestRaceFile(TestBase):
    def setUp(self):
        pass

    def tearDown(self):
        TestBase.delete_race_file()

    # Test that modifications to a race file can persist.
    def test_race_file_modify_race(self):
        TestBase.open_race_file()
        race = raceops.race_get()
        race['key'] = self.RACE_KEY
        race['value'] = self.RACE_VALUE
        raceops.race_modify(race)
        TestBase.close_race_file()

        TestBase.open_race_file()
        race2 = raceops.race_get()
        self.assertEqual(race, race2)
        TestBase.close_race_file()
