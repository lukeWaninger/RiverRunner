import datetime as dt
import numpy as np
import os
import psycopg2
from riverrunner import  settings
from riverrunner.daily import *
from riverrunner.repository import Repository
from riverrunner.tests.tcontext import TContext
from unittest import TestCase


class TestDaily(TestCase):
    @classmethod
    def setUpClass(cls):
        """perform at test class initialization

                Note:
                    * ensure only a TContext is used NEVER Context or we'll lose all
                    our hard-scraped data
                    * any existing data in the mock db will be deleted
                    * 5 random addresses are generated because nearly all unittests
                    require addresses to exist as a foreign key dependency
                """
        cls.context = TContext()
        cls.session = cls.context.Session()
        cls.connection = psycopg2.connect(**settings.PSYCOPG_DB_TEST)
        cls.repo = Repository(session=cls.session, connection=cls.connection)

        cls.context.clear_dependency_data(cls.session)
        cls.context.generate_addresses(cls.session)

    @classmethod
    def tearDownClass(cls):
        """perform when all tests are complete

        removes all data from the mock database
        """
        cls.context.clear_dependency_data(cls.session)
        cls.session.close()
        cls.connection.close()

    def setUp(self):
        """perform before each unittest"""
        self.session.flush()
        self.session.rollback()

    def tearDown(self):
        """perform after each unittest

        clears Prediction, StationRiverDistance, Measurement, Metric
        Station, RiverRun tables
        """
        self.context.clear_all_tables(self.session)

