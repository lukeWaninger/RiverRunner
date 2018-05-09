import requests

DATA_DIR = "data/"

USGS_BASE_URL = "https://waterservices.usgs.gov/nwis/iv/"
USGS_FORMAT = "json"
USGS_SITE_STATUS = "all"


def get_site_ids():
    site_ids = []
    with open(DATA_DIR + "site_ids.csv", "r") as f:
        site_ids = [line.strip() for line in f]
    return site_ids


def get_param_codes():
    param_codes = []
    with open(DATA_DIR + "param_codes.csv", "r") as f:
        param_codes = [line.strip() for line in f]
    return param_codes


def get_json_data(site_id, start_date, end_date, param_code):
    params = {
        "format": USGS_FORMAT,
        "sites": site_id,
        "startDT": start_date,
        "endDT": end_date,
        "parameterCd": param_code,
        "siteStatus": USGS_SITE_STATUS,
    }
    response_json = requests.get(USGS_BASE_URL, params=params).json()
    time_series_list = response_json["value"]["timeSeries"]
    values_list = []
    if len(time_series_list) > 0:
        values_list = time_series_list[0]["values"][0]["value"]
    date_value_map = {elem["dateTime"]: elem["value"] for elem in values_list}
    return date_value_map


def scrape_usgs_data(start_date, end_date):
    site_ids = get_site_ids()
    param_codes = get_param_codes()
    out_files = []
    for param_code in param_codes:
        out_file = DATA_DIR + "measurements_{}.csv".format(param_code)
        out_files.append(out_file)
        with open(out_file, "w") as f:
            for site_id in site_ids:
                json_data = get_json_data(
                    site_id,
                    start_date,
                    end_date,
                    param_code
                )
                for date_time, value in json_data.items():
                    f.write("{},{},{},{}\n".format(
                        site_id,
                        param_code,
                        date_time,
                        value
                    ))
    return out_files


def upload_data(csv_files):
    pass


if __name__ == "__main__":
    pass
