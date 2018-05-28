""" script that scrapes and uploads USGS data

Examples:
    python scrape_usgs_data.py [--csv] --manual start-date end-date

    * scrapes and uploads data over the specified date range (inclusive)
    * start-date and end-date must be in the format 'YYYY-MM-DD'
    * optional argument to insert records into database from CSV file

    python scrape_usgs_data.py [--csv] --daily [days-back]

    * scrapes and uploads data over date range
    * date range is from days-back before yesterday to yesterday (inclusive)
    * optional days-back parameter must be an integer (defaults to 0)
    * optional argument to insert records into database from CSV file
"""

import datetime
import dateutil
import json
import requests
import sys

from riverrunner import context
from riverrunner import repository


DATA_DIR = "data/"

USGS_BASE_URL = "https://waterservices.usgs.gov/nwis/iv/"
USGS_FORMAT = "json"
USGS_SITE_STATUS = "all"

PARAM_CODES = [
    "00021",
    "00045",
    "00060",
    "72147",
    "72254"
]

def get_site_ids():
    """ retrieve site ids from database

    Returns:
        [string]: list of site ids
    """
    r = repository.Repository()
    sites = r.get_all_stations(source="USGS")
    site_ids = [s for s in sites["station_id"]]
    return site_ids


def get_json_data(site_id, start_date, end_date, param_code):
    """ retrieve JSON data for a specific site, parameter, and date range

    Args:
        site_id (string): string representation of site id
        start_date (string): start date in the format 'YYYY-MM-DD'
        end_date (string): end date in the format 'YYYY-MM-DD'
        param_code (string): string representation of parameter code

    Returns:
        {string: string}: map relating timestamps to values
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
    #response_json = requests.get(USGS_BASE_URL, params=params).json()
    time_series_list = response_json["value"]["timeSeries"]
    values_list = []
    if len(time_series_list) > 0:
        values_list = time_series_list[0]["values"][0]["value"]
    date_value_map = {elem["dateTime"]: elem["value"] for elem in values_list}
    return date_value_map


def scrape_usgs_data(start_date, end_date):
    """ scrape data for all sites and parameters, over the specified date range

    Args:
        start_date (string): start date in the format 'YYYY-MM-DD'
        end_date (string): end date in the format 'YYYY-MM-DD'

    Returns:
        [string]: list of full paths of CSV files that were written to
    """
    start_date_file_ext = start_date.replace("-", "")
    end_date_file_ext = end_date.replace("-", "")
    site_ids = get_site_ids()
    param_codes = PARAM_CODES
    out_files = []
    for param_code in param_codes:
        total_values = 0
        out_file = DATA_DIR + "measurements_{}_{}_{}.csv".format(
            param_code,
            start_date_file_ext,
            end_date_file_ext
        )
        out_files.append(out_file)
        with open(out_file, "w") as f:
            for site_id in site_ids:
                json_data = get_json_data(
                    site_id=site_id,
                    start_date=start_date,
                    end_date=end_date,
                    param_code=param_code
                )
                total_values += len(json_data)
                for date_time, value in json_data.items():
                    f.write("{},{},{},{}\n".format(
                        site_id,
                        param_code,
                        date_time,
                        value
                    ))
        print("{}: {}".format(param_code, total_values))
    return out_files


def upload_data_from_file(csv_file, from_csv=False):
    """ insert all records contained in file to database

    Args:
        csv_file (string): full path of CSV file containing records
        from_csv (bool): whether to insert into database using CSV or ORM

    Returns:
        bool: success/exception
    """
    r = repository.Repository()

    if from_csv:
        success = r.put_measurements_from_csv(csv_file=csv_file)

    else:
        measurements = []
        with open(csv_file, "r") as f:
            for line in f:
                site_id, param_code, date_time, value = line.strip().split(",")
                measurement = context.Measurement(
                    station_id=site_id,
                    metric_id=param_code,
                    date_time=dateutil.parser.parse(date_time),
                    value=float(value)
                )
                measurements.append(measurement)
        success = r.put_measurements_from_list(measurements=measurements)

    return success


if __name__ == "__main__":
    # python scrape_usgs_data.py [--csv] --manual start-date end-date
    # python scrape_usgs_data.py [--csv] --daily [days-back]

    from_csv = False
    if sys.argv[1] == "--csv":
        from_csv = True

    if "--manual" in sys.argv[1:3]:
        index = sys.argv.index("--manual")
        start_date, end_date = sys.argv[index+1:]

    elif "--daily" in sys.argv[1:3]:
        index = sys.argv.index("--daily")
        days_back = 0
        if len(sys.argv) > index + 1:
            days_back = int(sys.argv[index+1])
        today = datetime.date.today()
        end_date = today - datetime.timedelta(days=1)
        start_date = end_date - datetime.timedelta(days=days_back)
        end_date = end_date.isoformat()
        start_date = start_date.isoformat()

    csv_files = scrape_usgs_data(start_date=start_date, end_date=end_date)
    for csv_file in csv_files:
        print("uploading {}...".format(csv_file))
        success = upload_data_from_file(csv_file=csv_file, from_csv=from_csv)
