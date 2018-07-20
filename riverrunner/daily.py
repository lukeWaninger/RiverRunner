"""Module to perform daily operations

There are two major methods to be used: daily_run, fill_gaps

daily run: retrieves weather data from the day prior then computes and inserts predictions for all river runs.
fill_gaps: the variables day and end can be modified as necessary to retrieve weather measurements between a
specified date range
"""

import os
from riverrunner.arima import Arima
from riverrunner.context import Prediction
from riverrunner.continuous_retrieval import *
from riverrunner.repository import Repository
from sqlalchemy.exc import SQLAlchemyError


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
    repo = Repository(db_context)

    fill_gaps(repo)
    compute_predictions(repo.session)


if __name__ == '__main__':
    # make sure the data and log dirs exist
    if not os.path.exists('data'):
        os.makedirs('data')
        os.makedirs('data/logs')
    elif not os.path.exists('data/logs'):
        os.makedirs('data/logs')

    daily_run(settings.DATABASE)
