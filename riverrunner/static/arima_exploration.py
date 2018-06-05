"""
Module for data exploration for ARIMA modeling.

This module contains the back-end exploration of river run flow rate data and exogenous
predictors to determine the best way to create a time-series model of the data. Note that
since this module was only used once (i.e. is not called in order to create ongoing
predictions), it is not accompanied by any unit testing.

Functions:
    daily_avg: takes time series with measurements on different timeframes and creates a
    dataframe with daily averages for flow rate and exogenous predictors

    test_stationarity: implements Dickey-Fuller test and rolling average plots to check
    for stationarity of the time series

    plot_autocorrs: creates plots of autocorrelation function and partial autocorrelation
    function to help determine p and q parameters for ARIMA model
"""

import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from riverrunner.repository import Repository
from statsmodels.tsa.arima_model import ARIMA
from statsmodels.tsa.stattools import acf, pacf
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.stattools import arma_order_select_ic

repo = Repository()


def daily_avg(time_series):
    """Creates dataframe needed for modelling

    Takes time series with measurements on different timeframes and creates a
    dataframe with daily averages for flow rate and exogenous predictors.

    Args:
        time_series: dataframe with metrics for one run_id, assumes output from
        get_measurements function

    Returns:
        DataFrame: containing daily measurements
    """
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

    time_series_daily = temp_daily.merge(flow_daily, how='inner',
                                         left_index=True, right_index=True)\
        .merge(precip_daily, how='inner', left_index=True, right_index=True)
    time_series_daily.columns = ['temp', 'flow', 'precip']
    return time_series_daily


def test_stationarity(time_series):
    """Visual and statistical tests to test for stationarity of flow rate.

    Performs Dickey-Fuller statistical test for stationarity at 0.05 level of
    significance and plots 12-month rolling mean and standard deviation against
    raw data for visual review of stationarity.

    Args:
        time_series: dataframe containing flow rate and exogneous predictor data for
        one river run (assumes output of daily_avg function).

    Returns:
        bool: True if data is stationary according to Dickey-Fuller test at
        0.05 level of significance, False otherwise.
        plot: containing rolling mean and standard deviation against raw data time series.

    """
    # Determine rolling statistics
    rollmean = time_series.rolling(window=365, center=False).mean()
    rollstd = time_series.rolling(window=365, center=False).std()

    # Plot rolling statistics
    plt.plot(time_series, color='blue', label='Raw Data')
    plt.plot(rollmean, color='red', label='Rolling Mean')
    plt.plot(rollstd, color='orange', label='Rolling Standard Deviation')
    plt.title('Rolling Statistics')
    plt.legend()
    plt.show()

    # Dickey-Fuller test
    dftest = adfuller(time_series, autolag='BIC')

    if dftest[0] < dftest[4]['1%']:
        return True
    else:
        return False


def plot_autocorrs(time_series):
    """
    Creates plots of auto-correlation function (acf) and partial auto-correlation function
    (pacf) to help determine p and q parameters for ARIMA model.

    Args:
        time_series: dataframe containing flow rate and exogneous predictor data for
        one river run (assumes output of daily_avg function).

    Returns:
        plots: containing acf and pacf of flow rate against number of lags.

    """
    lag_acf = acf(time_series['flow'], nlags=400)
    lag_pacf = pacf(time_series['flow'], method='ols')

    plt.subplot(121)
    plt.plot(lag_acf)
    plt.axhline(y=0, linestyle='--', color='gray')
    plt.axhline(y=-1.96 / np.sqrt(len(time_series)), linestyle='--', color='gray')
    plt.axhline(y=1.96 / np.sqrt(len(time_series)), linestyle='--', color='gray')
    plt.title('ACF')
    plt.subplot(122)
    plt.plot(lag_pacf)
    plt.axhline(y=0, linestyle='--', color='gray')
    plt.axhline(y=-1.96 / np.sqrt(len(time_series)), linestyle='--', color='gray')
    plt.axhline(y=1.96 / np.sqrt(len(time_series)), linestyle='--', color='gray')
    plt.title('PACF')
    plt.tight_layout()


# Retrieve data for one run to model
start = datetime.datetime(2014, 5, 18)
end = datetime.datetime(2018, 5, 17)
test_measures = repo.get_measurements(run_id=487, start_date=start, end_date=end)

# Average data and create train/test split
measures_daily = daily_avg(test_measures)
train_measures_daily = measures_daily[:-6]
test_measures_daily = measures_daily[-7:]
train_measures_daily = train_measures_daily.dropna()

# Check if data is stationary
test_stationarity(train_measures_daily['flow'])

# Determine p and q parameters for ARIMA model
params = arma_order_select_ic(train_measures_daily['flow'], ic='aic')

# Build and fit model
mod = ARIMA(train_measures_daily['flow'],
            order=(params.aic_min_order[0], 0, params.aic_min_order[1]),
            exog=train_measures_daily[['temp', 'precip']]).fit()
test_measures_daily.loc[:, 'prediction'] = \
    mod.forecast(steps=7, exog=test_measures_daily[['temp', 'precip']])[0]
train_measures_daily.loc[:, 'model'] = mod.predict()

# Plot results
plt.plot(test_measures_daily[['flow', 'prediction']])
plt.plot(train_measures_daily[['flow', 'model']]['2015-07':])
plt.legend(['Test values', 'Prediction', 'Train values', 'Model'])

