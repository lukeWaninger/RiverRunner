from riverrunner import context
from riverrunner.tests.tcontext import TContext
from unittest import TestCase


class TestContext(TestCase):
    """test class for database context

    Attributes:
        context (TContext): mock database context
        session (sqlalchemy.orm.sessionmaker): managed connection to that context
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

    def tearDown(self):
        """perform after each unittest

        clears Prediction, StationRiverDistance, Measurement, Metric
        Station, RiverRun tables
        """
        self.context.clear_all_tables(self.session)

    def test_add_prediction(self):
        """test adding a single prediction

        tests whether the prediction persists through session
        into backend
        """
        # setup
        predictions = self.context.get_predictions_for_test(1, self.session)
        self.session.add(predictions[0])
        self.session.commit()

        # assert
        predictions = self.session.query(context.Prediction).all()
        self.assertEqual(len(predictions), 1)

    def test_add_many_predictions(self):
        """test adding many predictions

        tests whether many predictions persist through session
        into backend within the same transaction
        """
        # setup
        predictions = self.context.get_predictions_for_test(10, self.session)
        self.session.add_all(predictions)
        self.session.commit()

        # assert
        predictions = self.session.query(context.Prediction).all()
        self.assertEqual(len(predictions), 10)

    def test_remove_prediction(self):
        """test removing a single prediction

        tests whether removing a single prediction persists
        through session into backend
        """
        # setup
        predictions = self.context.get_predictions_for_test(2, self.session)
        self.session.add_all(predictions)
        self.session.commit()

        self.session.query(context.Prediction).filter(
            context.Prediction.timestamp == predictions[0].timestamp
        ).delete()
        self.session.commit()

        # assert
        predictions = self.session.query(context.Prediction).all()
        self.assertEqual(len(predictions), 1)

    def test_remove_all_predictions(self):
        """test removing all predictions at once

        tests whether all predictions are removed from database
        during the same transaction
        """
        # setup
        predictions = self.context.get_predictions_for_test(10, self.session)
        self.session.add_all(predictions)
        self.session.commit()

        # assert
        self.session.query(context.Prediction).delete()
        predictions = self.session.query(context.Prediction).all()
        self.assertEqual(len(predictions), 0)

    def test_add_one_measurement(self):
        """test adding a single measurement

        tests whether the measurement persists through session
        into backend
        """
        # setup
        measurement = self.context.get_measurements_for_test(1, self.session)[0]
        self.session.add(measurement)
        self.session.commit()

        # assert
        measurements = self.session.query(context.Measurement).all()
        self.assertEqual(len(measurements), 1)

    def test_add_many_measurements(self):
        """test adding many measurements

        tests whether many measurements persist through session
        into backend within the same transaction
        """
        # setup
        measurements = self.context.get_measurements_for_test(10, self.session)
        self.session.add_all(measurements)
        self.session.commit()

        # assert
        measurements = self.session.query(context.Measurement).all()
        self.assertEqual(len(measurements), 10)

    def test_remove_measurement(self):
        """test removing a single measurement

        tests whether removing a single measurements persists
        through session into backend
        """
        # setup
        measurements = self.context.get_measurements_for_test(1, self.session)
        self.session.add(measurements[0])
        self.session.commit()

        # run
        self.session.delete(measurements[0])

        # assert
        measurements = self.session.query(context.Measurement).all()
        self.assertEqual(len(measurements), 0)
