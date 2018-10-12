import os
import raceops
import unittest

class TestRaceModel(unittest.TestCase):
    RACE_FILE='test.rce'
    RACE_NAME='San Bruno Hillclimb 2019'
    RACE_DATA='frhgfrhewgaourhewogihrgrhaewuigharueghorauwhg'

    def setUpClass():
        raceops.race_init(TestRaceModel.RACE_FILE)

    def tearDownClass():
        raceops.race_cleanup()
        try:
            os.remove(TestRaceModel.RACE_FILE)
        except OSError:
            pass

    # Test race_get(), race_modify()
    def test_race(self):
        race = raceops.race_get()
        self.assertEqual(race['name'], '(needs description)')

        race['name'] = TestRaceModel.RACE_NAME
        race['data'] = TestRaceModel.RACE_DATA
        raceops.race_modify(race)

        race2 = raceops.race_get()
        self.assertEqual(race2['name'], TestRaceModel.RACE_NAME)
        self.assertEqual(race2['data'], TestRaceModel.RACE_DATA)
