import os
import raceops
import unittest
from tests.testbase import TestBase

class TestRaceOpsBasic(TestBase):
    def setUpClass():
        TestBase.open_race_file()

    def tearDownClass():
        TestBase.close_race_file()
        TestBase.delete_race_file()

    # Test race_get(), race_modify()
    def test_race(self):
        race = raceops.race_get()
        self.assertEqual(race['name'], '(needs description)')

        race['name'] = TestBase.RACE_NAME
        race['data'] = TestBase.RACE_DATA
        raceops.race_modify(race)

        race2 = raceops.race_get()
        self.assertEqual(race2['name'], TestBase.RACE_NAME)
        self.assertEqual(race2['data'], TestBase.RACE_DATA)
