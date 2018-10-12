import raceimport
import unittest
from tests.testbase import TestBase

class TestRaceImport(TestBase):
    BIKEREG_CSV_FILE='tests/bikereg_sbhc2018.csv'

    def setUp(self):
        TestBase.open_race_file()

    def tearDown(self):
        TestBase.close_race_file()
        TestBase.delete_race_file()

    # Test race_get(), race_modify()
    def test_bikereg_csv_import(self):
        importer = raceimport.BikeRegRaceImporter()
        with open(self.BIKEREG_CSV_FILE) as import_file:
            importer.read(import_file)
