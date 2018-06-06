"""
Unit tests for arima module
"""
import unittest
import numpy as np
from riverrunner.arima import Arima
from riverrunner.context import Context
import riverrunner.settings as settings


class TestArima(unittest.TestCase):
    """test class for arima.py

    Attributes:
        arima (riverrunner.Arima): class being tested
    """
    @classmethod
    def setUpClass(cls):
        cls.context = Context(settings.DATABASE)
        cls.session = cls.context.Session()
        cls.arima = Arima(cls.session)

    def test_daily_avg_returns_correct_columns(self):
        """
        Tests that only flow, temp, and precip columns are present in
        dataframe and are spelled correctly. Important since arima_model
        function references these column names.
        Returns: result of test
        """
        # setup
        averages = self.arima.daily_avg(run_id=599)

        # assert
        self.assertTrue(set(averages.columns) ==
                        {'flow', 'temp', 'precip'})

    def test_daily_avg_returns_no_nans(self):
        """
        Ensure that datframe that will be passed to arima_model function
        does not contain any nans

        Returns: result of test
        """
        # setup
        averages = self.arima.daily_avg(run_id=599)

        # assert
        self.assertFalse(averages.isnull().any().any())

    def test_arima_model_returns_correct_days(self):
        """
        Test that arima_model function returns 7 predictions + 20
        past flow rates
        Returns: results of test
        """
        # setup
        predictions = self.arima.arima_model(run_id=386)

        # assert
        self.assertTrue(len(predictions) == 27)

    def test_arima_model_runs_if_order_select_fails(self):
        """
        Complete test for river run for which we know model order
        selection does not converge

        Returns: Result of test
        """
        try:
            self.arima.arima_model(run_id=600)
        except Exception:
            self.fail("arima_model() raised Exception unexpectedly")

    def test_arima_model_runs_if_arima_fails(self):
        """
        Complete test for river run for which we know ARIMA model
        does not converge

        Returns: Result of test
        """
        try:
            self.arima.arima_model(run_id=477)
        except Exception:
            self.fail("arima_model() raised Exception unexpectedly")

    def test_get_min_max_returns_correct_min(self):
        """
        Tests if function returns correct min value for known quantity

        Returns: Result of test
        """
        # setup
        levels = self.arima.get_min_max(477)

        # assert
        self.assertAlmostEquals(np.float(levels['min_level']), 800)

    def test_get_min_max_returns_correct_max(self):
        """
        Tests if function returns correct max value for known quantity

        Returns: Result of test
        """
        # setup
        levels = self.arima.get_min_max(477)

        # assert
        self.assertAlmostEquals(np.float(levels['max_level']), 6000)
