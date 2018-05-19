import datetime
import pandas as pd
import requests
from riverrunner.context import Context, Measurement
from riverrunner.repository import Repository
from riverrunner import settings
import sys
import time


def get_noaa_predictions(run_id, session):
    """retrieve noaa predictions for run

    Args
        run_id (int): run
        session (Session): database session

    Returns
        DataFrame: containing predictions
    """
    repo = Repository(session)
    run = repo.get_run(run_id)

    lat = run.put_in_latitude
    lon = run.put_in_longitude

    r = requests.get(f'https://api.weather.gov/points/{lat},{lon}/forecast/hourly')

    if r.status_code == 200 and len(r.content) > 10:
        return pd.DataFrame(r.json()['properties']['periods'])
    else:
        return None


def make_station_observation_request(station, day):
    """make a request for observations to the NOAA API

    Args:

    Returns:
        response
    """
    base = 'https://api.darksky.net/forecast'
    r = requests.get(f'{base}/{settings.DARK_SKY}/{station.latitude},{station.longitude},{day}')

    if r.status_code == 200:
        content = r.json()
        measurements = []

        # generate hourly measurements
        for obs in content['hourly']['data']:
            timestamp = obs['time']
            timestamp = datetime.datetime.fromtimestamp(timestamp)

            # add precip
            measurements.append(
                Measurement(
                    station_id=station.station_id,
                    metric_id='00003',
                    value=obs['precipIntensity'],
                    date_time=timestamp
                )
            )

            # add temp
            measurements.append(
                Measurement(
                    station_id=station.station_id,
                    metric_id='00001',
                    value=obs['temperature'],
                    date_time=timestamp
                )
            )

            # add humidity
            measurements.append(
                Measurement(
                    station_id=station.station_id,
                    metric_id='00002',
                    value=obs['humidity'],
                    date_time=timestamp
                )
            )

        return measurements
    else:
        return None


def put_24hr_observations(session):
    """get yesterdays observations

    Args
        session (Session): database session
    """
    repo = Repository(session)
    stations = repo.get_all_stations()

    yesterday = datetime.datetime.now() - datetime.timedelta(hours=24)
    yesterday = datetime.datetime(year=yesterday.year, month=yesterday.month, day=yesterday.day)

    content = stations.apply(
        lambda station: make_station_observation_request(station, yesterday.isoformat()),
        axis=1
    ).values

    # put them all in the db
    added = 0
    for station_measurements in content:
        repo.put_measurements_from_list(station_measurements)
        added += len(station_measurements)
    
    return added


def daily_run(attempt=0):
    """input the past 24 hr observations and write to log"""
    try:
        if attempt >= settings.DARK_SKY_RETRIES:
            return 1

        context = Context(settings.DATABASE_TEST)
        session = context.Session()
        
        added = put_24hr_observations(session)
        session.close()
        
        with open('observation_log.txt', 'a+') as f:
            f.write(f'{datetime.datetime.now().isoformat()}: added {added} observations to db\n')

        sys.exit(0)
    except:
        with open('observation_log.txt', 'a+') as f:
            f.write(f'{datetime.datetime.now().isoformat()}: failed to pull past 24hr measurements\n')
        time.sleep(600)
        daily_run(attempt+1)
        sys.exit(1)


if __name__ == '__main__':
    daily_run(0)