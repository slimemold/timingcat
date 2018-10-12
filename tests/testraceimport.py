import raceimport
import raceops
import unittest
from tests.testbase import TestBase

class TestRaceImport(TestBase):
    BIKEREG_CSV_FILE='tests/bikereg_sbhc2018.csv'
    TOTAL_FIELDS=14
    TOTAL_RACERS=104

    def setUp(self):
        TestBase.open_race_file()

    def tearDown(self):
        TestBase.close_race_file()
        TestBase.delete_race_file()

    def test_bikereg_csv_import(self):
        importer = raceimport.BikeRegRaceImporter()
        with open(self.BIKEREG_CSV_FILE) as import_file:
            importer.read(import_file)

        field_list = raceops.field_get_list()
        self.assertEqual(len(field_list), self.TOTAL_FIELDS)

        racer_list = raceops.racer_get_list()
        self.assertEqual(len(racer_list), self.TOTAL_RACERS)  
