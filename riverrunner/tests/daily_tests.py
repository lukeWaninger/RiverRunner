import os
import psycopg2
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

    def test_log(self):
        message = 'write this'
        log(message)

        now = dt.datetime.today()
        path = f'data/logs/{now.year}{now.month}{now.day}_log.txt'

        with open(path) as f:
            line = f.readline()

        self.assertTrue(line.find(message) > 0)
        os.remove(path)

    def test_get_weather_obs_breaks_recursion(self):
        c = get_weather_observations(self.session, 0, 0)
        self.assertEqual(c, 1)

    def test_get_weather_obs_returns_correctly(self):
        station = self.context.get_stations_for_test(1, self.session)[0]
        metric = self.context.get_metrics_for_test(3)
        metric[0].metric_id = 3
        metric[1].metric_id = 2
        metric[2].metric_id = 1

        self.session.add_all([station, metric[0], metric[1], metric[2]])

        m = get_weather_observations(self.session)
        self.assertTrue(m)

    def test_get_weather_gracefully_exits(self):
        station = self.context.get_stations_for_test(1, self.session)[0]
        self.session.add(station)

        m = get_weather_observations(session=self.session, retries=1, wait=0)
        self.assertTrue(m)

    def test_get_weather_gracefully_fails_for_anything(self):
        m = get_weather_observations(self.session, attempt=[False, False], retries=1, wait=0)
        self.assertTrue(not m)

    def test_get_usgs_obs(self):
        pass

    def test_compute_predictions_no_runs_present(self):
        m = compute_predictions(self.session)
        self.assertTrue(m)

    def test_compute_predictions_fails_one_run(self):
        run = self.context.get_runs_for_test(1, self.session)[0]
        self.session.add(run)

        m = compute_predictions(self.session)
        now = dt.datetime.today()
        path = f'data/logs/{now.year}{now.month}{now.day}_log.txt'

        with open(path) as f:
            line = f.readline()

        self.assertTrue(not (line.find('failed') > 0))

    def test_compute_predictions_for_one_run(self):
        run = self.context.get_runs_for_test(1, self.session)[0]
        station = self.context.get_stations_for_test(1, self.session)[0]
        metrics = self.context.get_metrics_for_test(3)
        metrics[0].metric_id = '00003'
        metrics[1].metric_id = '00001'
        metrics[2].metric_id = '00060'

        self.session.add_all([run, station])
        self.session.add_all(metrics)
        self.session.commit()

        m = compute_predictions(self.session)
        self.assertTrue(m)
