"""Module to perform daily operations

There are two major methods to be used: daily_run, fill_gaps

daily run: retrieves weather data from the day prior then computes and inserts predictions for all river runs.
fill_gaps: the variables day and end can be modified as necessary to retrieve weather measurements between a
specified date range
"""

from riverrunner.arima import Arima
from riverrunner.context import Prediction
from riverrunner import continuous_retrieval
from riverrunner.continuous_retrieval import *
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

    now = dt.datetime.today()
    with open(f'data/logs/{now.year}{now.month}{now.day}_log.txt', 'w+') as f:
        f.write(f'{dt.datetime.now().isoformat()}: {message}\n')


def get_weather_observations(session, attempt=0, retries=DARK_SKY_RETRIES, wait=DARK_SKY_WAIT):
    """input the past 24 hr observations and write to log

    Args:
        session: (Session) database connection
        attempt: (int) optional maximum retries for API call
        retries: (int) optional number of API retries
        wait: (int) optional seconds between attempts
    Returns:
        True: if observations were successfully retrieved and inserted
        False: otherwise
    """
    try:
        if attempt >= retries:
            return 1
        added = continuous_retrieval.put_24hr_observations(session)

        log(f'added {added} observations to db')
        return True

    except SQLAlchemyError as e:
        session.rollback()
        log(f'failed to gather daily observations - {str(e.args)}')
        time.sleep(wait)

        return get_weather_observations(session, attempt+1)

    except Exception as e:
        log(f'failed to gather daily observations - {str(e.args)}')
        return False


def get_usgs_observations():
    """retrieves yesterday's USGS river metrics"""
    yesterday = dt.date.today() - dt.timedelta(days=1)
    end_date = yesterday.isoformat()

    csv_files = scrape_usgs_data(start_date=end_date, end_date=end_date)
    for csv_file in csv_files:
        log("uploading {}...".format(csv_file))
        upload_data_from_file(csv_file=csv_file)

    return True


def compute_predictions(session):
    """compute and cache predictions for all runs

    Args:
        session: (Session) database connection

    Returns:
        True: if observations were successfully retrieved and inserted
        False: otherwise
    """
    try:
        arima = Arima(session)
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

        return True

    except Exception as e:
        log(f'failed to compute daily predictions - {str(e.args)}')
        return False


def daily_run(db_context):
    """perform the daily observation retrieval and flow rate predictions"""
    context = Context(db_context)
    session = context.Session()

    get_weather_observations(session)
    get_usgs_observations()
    compute_predictions(session)

    session.close()


if __name__ == '__main__':
    daily_run(settings.DATABASE)
