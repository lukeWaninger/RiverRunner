from multiprocessing import Process
from riverrunner.ui import *
from riverrunner.tests.tcontext import TContext
from unittest import TestCase


class TestRepository(TestCase):
    """test class for continous noaa integration

    Attributes:
        context(TContext): mock database context
        session (Session): managed connection to that context
        repo(riverrunner.Repository):
    """

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

        cls.context.clear_dependency_data(cls.session)
        cls.context.generate_addresses(cls.session)

    @classmethod
    def tearDownClass(cls):
        """perform when all tests are complete

        removes all data from the mock database
        """
        cls.context.clear_dependency_data(cls.session)
        cls.session.close()

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

    def test_ui(self):
        p = Process(target=run_ui)
        p.start()

        self.assertTrue(p.is_alive())
        p.terminate()
