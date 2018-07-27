""" script that scrapes and uploads DarkSky and USGS data

Examples:
    python continuous_retrieval.py [--csv] --manual start-date end-date

    * scrapes and uploads data over the specified date range (inclusive)
    * start-date and end-date must be in ISO format, 'YYYY-MM-DD'
    * optional argument to insert records into database from CSV file (for USGS data only)

    python continuous_retrieval.py [--csv] --daily [days-back]

    * scrapes and uploads data over date range
    * date range is from days-back before yesterday to yesterday (inclusive)
    * optional days-back parameter must be an integer (defaults to 0)
    * optional argument to insert records into database from CSV file (for USGS data only)
"""
import datetime as dt
import json
import pandas as pd
import re
import requests
from riverrunner import settings
from riverrunner.context import Context, Measurement
from riverrunner.repository import Repository
from tqdm import tqdm


# data directory
DATA_DIR = "data/"

# base API URLs
DARK_SKY_URL = 'https://api.darksky.net/forecast'
USGS_BASE_URL = "https://waterservices.usgs.gov/nwis/iv/"

# USGS query constants
USGS_FORMAT = "json"
USGS_SITE_STATUS = "all"

# USGS parameter codes
PARAM_CODES = [
    '00003', '00060', '00001'
]


def fill_noaa_gaps(start_date, end_date, db=settings.DATABASE):
    """use as needed to fill gaps in weather measurements

    Args:
        start_date: the start day, included in API calls
        end_date: the end day, inclusive
    """
    context = Context(db)
    session = context.Session()

    repo = Repository(session)
    stations = repo.get_all_stations(source='NOAA')
    measurements = []

    # loop through each day retrieving observations
    while start_date <= end_date:
        content = stations.apply(
            lambda station: make_station_observation_request(station, start_date.isoformat()),
            axis=1
        ).values

        # flatten them out
        for station_measurements in content:
            measurements += station_measurements

        print(f'{start_date} complete')
        start_date += dt.timedelta(days=1)

    return measurements


def get_noaa_predictions(run_id, session):
    """retrieve NOAA predictions for run

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


def get_usgs_site_ids():
    """ retrieve USGS site ids from database

    Returns:
        [str]: list of site ids
    """
    r = Repository()
    sites = r.get_all_stations(source="USGS")
    site_ids = [s for s in sites["station_id"]]
    return site_ids


def get_usgs_json_data(site_id, start_date, end_date, param_code):
    """ retrieve JSON data for a specific USGS site, parameter, and date range

    Args:
        site_id (str): string representation of site id
        start_date (str): start date in ISO format, 'YYYY-MM-DD'
        end_date (str): end date in ISO format, 'YYYY-MM-DD'
        param_code (str): string representation of parameter code

    Returns:
        dict[str, str]: map relating timestamps to values
    """
    params = {
        "format": USGS_FORMAT,
        "sites": site_id,
        "startDT": start_date,
        "endDT": end_date,
        "parameterCd": param_code,
        "siteStatus": USGS_SITE_STATUS,
    }
    response = requests.get(USGS_BASE_URL, params=params)
    try:
        response_json = response.json()
    except json.decoder.JSONDecodeError:
        print(response.content)
        raise
    # response_json = requests.get(USGS_BASE_URL, params=params).json()
    time_series_list = response_json["value"]["timeSeries"]
    values_list = []
    if len(time_series_list) > 0:
        values_list = time_series_list[0]["values"][0]["value"]
    date_value_map = {elem["dateTime"]: elem["value"] for elem in values_list}
    return date_value_map


def make_station_observation_request(station, day):
    """make a request for observations to the DarkSky API

    Args:
        station: (Station) weather station to retrieve measurments
        day: (str) datetime in iso format
    Returns:
        [Measurements] if call was successful
        None otherwise
    """
    now = dt.datetime.now().isoformat()

    r = requests.get(f'{DARK_SKY_URL}/{settings.DARK_SKY_KEY}/{station.latitude},{station.longitude},{day}')

    # make sure the web result is valid
    if r.status_code == 200:
        content = r.json()
        measurements = []

        # generate hourly measurements
        for obs in content['hourly']['data']:
            timestamp = obs['time']
            timestamp = dt.datetime.fromtimestamp(timestamp)

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
        print(f'{now}: {station.station_id} failed')
        return None


def scrape_usgs_data(start_date, end_date):
    """ scrape data for all USGS sites and parameters, over the specified date range

    Args:
        start-date (str): end date in ISO format, 'YYYY-MM-DD'

    Returns:
        [str]: list of full paths of CSV files that were written to
    """
    site_ids = get_usgs_site_ids()
    param_codes = PARAM_CODES

    measurements = []
    for param_code in param_codes:
        print(f'\nmaking station observation requests for param code: {param_code}')

        for site_id in tqdm(site_ids, desc='converting USGS JSON to SQL'):
            json_data = get_usgs_json_data(
                site_id=site_id,
                start_date=start_date,
                end_date=end_date,
                param_code=param_code
            )

            for date_time, value in json_data.items():
                tz = date_time[date_time.find(':', 17)-3:]
                date_time = re.sub(tz, '', date_time)

                tz = re.sub(':', '', tz)
                date_time = dt.datetime.strptime(f'{date_time}{tz}', '%Y-%m-%dT%H:%M:%S.%f%z')

                measurements.append(
                    Measurement(
                        station_id=site_id,
                        metric_id=param_code,
                        date_time=date_time,
                        value=float(value)
                    )
                )

    print(f'pulled {len(measurements)} USGS measurements')
    return measurements


def fill_gaps(repository, start_date=None, end_date=None):
    now = dt.datetime.now()

    # check for start date
    if start_date is None:
        start_date = dt.datetime(year=now.year, month=now.month, day=now.day) - dt.timedelta(days=1)
    else:
        pass

    # end for end date
    if end_date is None:
        end_date = dt.datetime(year=now.year, month=now.month, day=now.day)
    else:
        pass

    # get new data
    measurements = fill_noaa_gaps(start_date, end_date)
    measurements = [] if measurements is None else measurements

    measurements += scrape_usgs_data(
        start_date=start_date.strftime(format='%Y-%m-%d'),
        end_date=end_date.strftime(format='%Y-%m-%d')
    )

    # upload to aws
    repository.put_measurements(measurements=measurements)


if __name__ == "__main__":
    repo = Repository()

    fill_gaps(
        repo,
        start_date=dt.datetime(year=2018, month=7, day=25),
        end_date=dt.datetime(year=2018, month=7, day=26)
    )
