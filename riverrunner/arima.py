"""
Module for ARIMA modeling.

Classes:
    Arima: contains functions to retrieve data and build ARIMA model for given river run
        Functions:
            get_data: retrieves needed data for selected run

            daily_avg: takes time series with measurements on different timeframes and
            creates a dataframe with daily averages for flow rate and exogenous predictors

            arima_model: creates flow rate predictions using statsmodel package functions

            get_min_max: use get_all_runs function to query database and then pull min and
            max runnable flow rate for given run
"""

import datetime
import pandas as pd
from riverrunner.repository import Repository
from statsmodels.tsa.arima_model import ARIMA
from statsmodels.tsa.stattools import arma_order_select_ic

repo = Repository()


class Arima:
    """
    Creates predictions for future flow rate using ARIMA model
    """
    def get_data(self, run_id):
        """Retrieves data for selected run from database for past four years
        from current date using Repository.get_measurements function.

        Args:
            run_id (int): id of run for which model will be created

        Returns:
            DataFrame: containing four years of measurements up to current date
            for the given run
        """
        now = datetime.datetime.now()
        end = datetime.datetime(now.year, now.month, now.day)
        start = end - datetime.timedelta(days=4*365)
        test_measures = repo.get_measurements(run_id=run_id, start_date=start, end_date=end)
        return test_measures

    def daily_avg(self, run_id):
        """Creates dataframe needed for modelling

        Calls Arima.get_data to retrieve measurements for given run and creates a
        dataframe with daily averages for flow rate and exogenous predictors.

        Args:
            run_id (int): id of run for which model will be created

        Returns:
            DataFrame: containing daily measurements
        """
        time_series = self.get_data(run_id=run_id)

        precip = time_series[time_series.metric_id == '00003']
        precip['date_time'] = pd.to_datetime(precip['date_time'], utc=True)
        precip.index = precip['date_time']
        precip_daily = precip.resample('D').sum()

        flow = time_series[time_series.metric_id == '00060']
        flow['date_time'] = pd.to_datetime(flow['date_time'], utc=True)
        flow.index = flow['date_time']
        flow_daily = flow.resample('D').mean()

        temp = time_series[time_series.metric_id == '00001']
        temp['date_time'] = pd.to_datetime(temp['date_time'], utc=True)
        temp.index = temp['date_time']
        temp_daily = temp.resample('D').mean()

        time_series_daily = temp_daily.merge(flow_daily, how='inner', left_index=True,
                                             right_index=True)\
            .merge(precip_daily, how='inner', left_index=True, right_index=True)
        time_series_daily.columns = ['temp', 'flow', 'precip']
        time_series_daily = time_series_daily.dropna()
        return time_series_daily

    def arima_model(self, run_id):
        """Creates flow rate predictions using ARIMA model.

        Calls Arima.daily_avg to retrieve data for given run, then creates flow rate
        predictions by using statsmodels functions arma_order_select_ic and ARIMA.
        Three weeks of past flow rate data are also returned for plotting purposes.

        Args:
            run_id (int): id of run for which model will be created

        Returns:
            DataFrame: containing time-series flow rate predictions for next 7 days and
            historical flow rate for past 21 days
        """
        # Retrieve data for modelling
        measures = self.daily_avg(run_id)

        # Take past 7-day average of exogenous predictors to use for future prediction
        exog_future_predictors = pd.concat([measures.iloc[-7:, :].mean(axis=0).to_frame().T]*7,
                                           ignore_index=True)

        try:
            # Find optimal order for model
            params = arma_order_select_ic(measures['flow'], ic='aic')
            try:
                # Build and fit model
                mod = ARIMA(measures['flow'],
                            order=(params.aic_min_order[0], 0, params.aic_min_order[1]),
                            exog=measures[['temp', 'precip']]).fit()
                prediction = pd.DataFrame(
                    [mod.forecast(steps=7, exog=exog_future_predictors[['temp', 'precip']],
                                                        alpha=0.05)[0]]).T
            except Exception:
                # If model doesn't converge, return "prediction" of most recent day
                prediction = pd.concat([measures.iloc[-1, :].to_frame().T] * 7,
                                       ignore_index=True)['flow']
        except ValueError:
            # If order fitting doesn't converge, return "prediction" of most recent day
            prediction = pd.concat([measures.iloc[-1, :].to_frame().T] * 7,
                                   ignore_index=True)['flow']

        # Add dates and return past 21 days for plotting
        prediction_dates = [measures.index[-2] + datetime.timedelta(days=x) for x in range(0, 7)]
        prediction.index = prediction_dates
        past = measures['flow'][-22:-1]
        prediction = pd.concat([past, prediction], axis=0)
        return prediction

    def get_min_max(self, run_id):
        """Gets min and max runnable flow rate for river run to use for plots

        Args:
            run_id: id of run for which model will be created

        Returns:
            levels: minimum and maximum runnable flow rate for river
        """
        runs = repo.get_all_runs()
        levels = runs[['min_level', 'max_level']][runs['run_id'] == run_id]
        return levels
