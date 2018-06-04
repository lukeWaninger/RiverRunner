"""Module to perform daily operations

There are two major methods to be used: daily_run, fill_gaps

daily run: retrieves weather data from the day prior then computes and inserts predictions for all river runs.
fill_gaps: the variables day and end can be modified as necessary to retrieve weather measurements between a
specified date range
"""

import datetime as dt
import pandas as pd
from riverrunner.arima import Arima
from riverrunner.context import Context, Prediction
from riverrunner import continuous_noaa, settings
from riverrunner.scrape_usgs_data import *
from riverrunner.repository import Repository
from sqlalchemy.exc import SQLAlchemyError
import time

"""maximum number of API retries for Dark Sky"""
DARK_SKY_RETRIES = 10

"""wait time in seconds between API call"""
DARK_SKY_WAIT = 600


def log(message):
    """write log message to file

    all logs are written to the directory data/logs with the filename in the format YYYMMDD_log.txt

    Args:
        message: (str) message to write
    """
    print(message)

    now = datetime.datetime.today()
    with open(f'data/logs/{now.year}{now.month}{now.day}_log.txt', 'a+') as f:
        f.write(f'{datetime.datetime.now().isoformat()}: {message}\n')


def get_weather_observations(session, attempt=0):
    """input the past 24 hr observations and write to log

    Args:
        session: (Session) database connection
        attempt: (int) optional maximum retries for API call

    Returns:
        True: if observations were successfully retrieved and inserted
        False: otherwise
    """
    try:
        if attempt >= DARK_SKY_RETRIES:
            return 1
        added = continuous_noaa.put_24hr_observations(session)

        log(f'added {added} observations to db')
        return True

    except SQLAlchemyError as e:
        session.rollback()
        log(f'failed to gather daily observations - {str(e.args)}')
        time.sleep(DARK_SKY_WAIT)
        get_weather_observations(session, attempt+1)

    except Exception as e:
        log(f'failed to gather daily observations - {str(e.args)}')
        time.sleep(DARK_SKY_WAIT)
        get_weather_observations(session, attempt+1)
        return False


def get_usgs_observations():
    """retrieves yesterday's USGS river metrics"""
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    end_date = yesterday.isoformat()

    csv_files = scrape_usgs_data(start_date=end_date, end_date=end_date)
    for csv_file in csv_files:
        log("uploading {}...".format(csv_file))
        upload_data_from_file(csv_file=csv_file)


def compute_predictions(session):
    """compute and cache predictions for all runs

    Args:
        session: (Session) database connection

    Returns:
        True: if observations were successfully retrieved and inserted
        False: otherwise
    """
    try:
        arima = Arima()
        repo = Repository(session)

        runs = repo.get_all_runs_as_list()
        for run in runs:
            try:
                predictions = arima.arima_model(run.run_id)

                to_add = [
                    Prediction(
                        run_id=run.run_id,
                        timestamp=pd.to_datetime(d),
                        fr_lb=round(float(p), 1),
                        fr=round(float(p), 1),
                        fr_ub=round(float(p), 1)
                    )
                    for p, d in zip(predictions.values, predictions.index.values)
                ]

                repo.clear_predictions(run.run_id)
                repo.put_predictions(to_add)
                log(f'predictions for {run.run_id}-{run.run_name} added to db')
                return True

            except SQLAlchemyError as e:
                log(f'{run.run_id}-{run.run_name} failed - {[str(a) for a in e.args]}')
                session.rollback()

            except Exception as e:
                log(f'predictions for {run.run_id}-{run.run_name} failed - {[str(a) for a in e.args]}')

    except Exception as e:
        log(f'failed to compute daily predictions - {str(e.args)}')
        return False


def daily_run():
    """perform the daily observation retrieval and flow rate predictions"""
    context = Context(settings.DATABASE)
    session = context.Session()

    get_weather_observations(session)
    get_usgs_observations()
    compute_predictions(session)

    session.close()


def fill_gaps():
    """use as needed to fill gaps in weather measurements

    Notes:
        * day: the start day, included in API calls
        * end: th end day, non-inclusive
    """
    day = dt.datetime(year=2018, month=5, day=18)
    end = dt.datetime(year=2018, month=5, day=19)

    context = Context(settings.DATABASE)
    session = context.Session()

    repo = Repository(session)
    stations = repo.get_all_stations(source='NOAA')

    while day != end:
        content = stations.apply(
            lambda station: continuous_noaa.make_station_observation_request(station, day.isoformat()),
            axis=1
        ).values

        # put them all in the db
        added = 0
        for station_measurements in content:
            try:
                repo.put_measurements_from_list(station_measurements)
            except:
                session.rollback()
                continue
            added += len(station_measurements)

        print(f'added {added} - {day.isoformat()}')
        day += datetime.timedelta(days=1)


if __name__ == '__main__':
    daily_run()
