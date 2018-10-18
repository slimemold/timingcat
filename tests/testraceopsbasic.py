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
        self.assertEqual(race['key'], 'Race name')
        self.assertEqual(race['value'], '(needs description)')

        race['key'] = TestBase.RACE_KEY
        race['value'] = TestBase.RACE_VALUE
        raceops.race_modify(race)

        race2 = raceops.race_get()
        self.assertEqual(race2['key'], TestBase.RACE_KEY)
        self.assertEqual(race2['value'], TestBase.RACE_VALUE)
