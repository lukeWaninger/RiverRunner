from riverrunner import context
from riverrunner.tests.tcontext import TContext
from unittest import TestCase


class TestContext(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = TContext()
        cls.session = cls.context.Session()

        cls.context.clear_dependency_data(cls.session)
        cls.context.generate_addresses(cls.session)

    @classmethod
    def tearDownClass(cls):
        cls.context.clear_dependency_data(cls.session)
        cls.session.close()

    def tearDown(self):
        self.context.clear_all_tables(self.session)

    def test_add_prediction(self):
        # setup
        predictions = self.context.get_predictions_for_test(1, self.session)
        self.session.add(predictions[0])
        self.session.commit()

        # assert
        predictions = self.session.query(context.Prediction).all()
        self.assertEqual(len(predictions), 1)

    def test_add_many_predictions(self):
        # setup
        predictions = self.context.get_predictions_for_test(10, self.session)
        self.session.add_all(predictions)
        self.session.commit()

        # assert
        predictions = self.session.query(context.Prediction).all()
        self.assertEqual(len(predictions), 10)

    def test_remove_prediction(self):
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
        # setup
        predictions = self.context.get_predictions_for_test(10, self.session)
        self.session.add_all(predictions)
        self.session.commit()

        # assert
        self.session.query(context.Prediction).delete()
        predictions = self.session.query(context.Prediction).all()
        self.assertEqual(len(predictions), 0)

    def test_add_one_measurement(self):
        # setup
        measurement = self.context.get_measurements_for_test(1, self.session)[0]
        self.session.add(measurement)
        self.session.commit()

        # assert
        measurements = self.session.query(context.Measurement).all()
        self.assertEqual(len(measurements), 1)

    def test_add_many_measurements(self):
        # setup
        measurements = self.context.get_measurements_for_test(10, self.session)
        self.session.add_all(measurements)
        self.session.commit()

        # assert
        measurements = self.session.query(context.Measurement).all()
        self.assertEqual(len(measurements), 10)

    def test_remove_measurement(self):
        # setup
        measurements = self.context.get_measurements_for_test(1, self.session)
        self.session.add(measurements[0])
        self.session.commit()

        # run
        self.session.delete(measurements[0])

        # assert
        measurements = self.session.query(context.Measurement).all()
        self.assertEqual(len(measurements), 0)
