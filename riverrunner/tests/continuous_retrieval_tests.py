import datetime as dt
from riverrunner.context import Address, Metric, RiverRun, Station
from riverrunner.continuous_retrieval import *
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

    def test_get_noaa_predictions(self):
        """test that predictions are returned"""
        # setup
        address = Address(
            latitude=45.624,
            longitude=-122.306
        )

        run = RiverRun(
            run_id=1,
            put_in_latitude=address.latitude,
            put_in_longitude=address.longitude,
            take_out_latitude=address.latitude,
            take_out_longitude=address.longitude
        )

        self.session.add_all([address, run])
        self.session.commit()

        predictions = get_noaa_predictions(run.run_id, self.session)

        # assert
        self.assertIsInstance(predictions, pd.DataFrame)
        self.assertTrue(len(predictions.columns) > 0)

    def test_make_station_observation_request(self):
        """test a request to NOAA for observations"""
        a = self.session.query(Measurement).filter(
            Measurement.date_time >= dt.datetime.now() - dt.timedelta(days=24)
        ).all()

        address1 = Address(
            latitude=46.65,
            longitude=-119.91
        )
        station1 = Station(
            station_id='KAWO',
            latitude=address1.latitude,
            longitude=address1.longitude,
            source='NOAA'
        )

        address2 = Address(
            latitude=47.63333,
            longitude=-117.65
        )
        station2 = Station(
            station_id='KGEG',
            latitude=address2.latitude,
            longitude=address2.longitude,
            source='NOAA'
        )

        self.session.add_all([
            address1, address2,
            station1, station2,
            Metric(metric_id='00003'),
            Metric(metric_id='00002'),
            Metric(metric_id='00001')
        ])
        self.session.commit()

        put_24hr_observations(self.session)

        # assert
        b = self.session.query(Measurement).filter(
            Measurement.date_time >= dt.datetime.now() - dt.timedelta(days=24)
        ).all()
        self.assertTrue(len(b) > len(a))

    def test_get_usgs_site_ids(self):
        """test that USGS station ids get retrieved"""
        # assert
        site_ids = get_usgs_site_ids()
        self.assertTrue(len(site_ids) != 0)

    def test_get_usgs_json_data(self):
        """test a successful request is made to USGS API"""
        site_id = "12010000"
        start_date = "2018-01-01"
        end_date = start_date
        param_code = PARAM_CODES[0]

        # assert
        date_value_map = get_usgs_json_data(site_id, start_date, end_date, param_code)
        self.assertTrue(len(date_value_map) != 0)
