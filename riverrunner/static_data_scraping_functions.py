"""
Module for static data retrieval. These functions were performed once during the initial project creation. Resulting
data is now provided in bulk at the url above.
"""

import datetime
import json
from math import sin, cos, sqrt, atan2, radians
import re
import requests
import pandas as pd
from riverrunner import settings
from riverrunner.context import StationRiverDistance
from riverrunner.repository import Repository


def scrape_rivers_urls():
    """scrape river run data from Professor Paddle

    generates URLs from the array of strings below. Each element represents a unique river. Each page is
    requested with the entire HTML contents being saved to disk. The parsed river data is saved to 'data/rivers.csv'
    """
    # copied from jquery selection in chrome dev tools on main prof paddle run table
    river_links = pd.read_csv('riverrunner/data/static_river_urls.csv').columns.values

    river_ids = [r[r.find("=")+1:] for r in river_links]
    url = "http://www.professorpaddle.com/rivers/riverdetails.asp?riverid="

    for id in river_ids:
        r = requests.get(url + id)

        if r.status_code == 200:
            with open("river_%s.html" % id, 'w+') as f:
                f.write(str(r.content))

    rivers = []
    for rid in river_ids:
        with open('data/river_%s.html' % rid) as f:
            river = f.readlines()

        r = river[0]

        row = {}
        # title and river name
        r = r[r.find('<font size="+2">'):]
        run_name = r[r.find(">") + 1:r.find('<a')]
        run_name = re.sub(r'<[^>]*>|&nbsp;', ' ', run_name)

        river_name = run_name[:run_name.find(' ')]
        run_name = run_name[len(river_name):]
        run_name = re.sub(r'&#039;', "'", run_name)
        run_name = re.sub(r'&#8212;', "", run_name).strip()
        row['run_name'] = re.sub(r'(  )+', ' ', run_name)
        row['river_name'] = river_name

        # chunk off the class
        r = r[r.find('Class'):]
        rating = r[6:r.find('</strong>')]
        row['class_rating'] = rating

        # river length
        r = r[r.find('<strong>')+8:]
        length = r[:r.find("<")]
        row['river_length'] = length

        # zip code
        r = r[r.find('Zip Code'):]
        r = r[r.find('path')+6:]
        row['zip'] = r[:r.find("<")]

        # put in long
        r = r[r.find("Put In Longitude"):]
        r = r[r.find('path')+6:]
        row['put_in_long'] = r[:r.find("<")]

        # put in lat
        r = r[r.find("Put In Latitude"):]
        r = r[r.find('path')+6:]
        row['put_in_lat'] = r[:r.find("<")]

        # take out long
        r = r[r.find("Take Out Longitude"):]
        r = r[r.find('path')+6:]
        row['take_out_long'] = r[:r.find("<")]

        # take out lat
        r = r[r.find("Take Out Latitude"):]
        r = r[r.find('path')+6:]
        row['take_out_lat'] = r[:r.find("<")]

        # county
        r = r[r.find("County"):]
        r = r[r.find('path')+6:]
        row['county'] = r[:r.find("<")]

        # min level
        r = r[r.find("Minimum Recomended Level"):]
        r = r[r.find("&nbsp;")+6:]
        row['min_level'] = r[:r.find("&")]

        # min level units
        r = r[r.find(';')+1:]
        row['min_level_units'] = r[:r.find('&')]

        # Maximum Recomended Level
        r = r[r.find("Maximum Recomended Level"):]
        r = r[r.find("&nbsp;")+6:]
        row['max_level'] = r[:r.find("&")]

        # max level units
        r = r[r.find(';')+1:]
        row['max_level_units'] = r[:r.find('&')]

        row['id'] = rid
        row['url'] = url + rid
        rivers.append(row)

    pd.DataFrame(rivers).to_csv('data/rivers.csv')


def parse_location_components(components, lat, lon):
    """parses location data from a Goggle address component list"""
    location = {'latitude': lat, 'longitude': lon}

    for component in components:
        component_type = component['types']

        if 'route' in component_type:
            location['address'] = component['long_name']

        elif 'locality' in component_type:
            location['city'] = component['long_name']

        elif 'administrative_area_level_2' in component_type:
            location['route'] = re.sub(r'County', '', component['long_name'])

        elif 'administrative_area_level_1' in component_type:
            location['state'] = component['short_name']

        elif 'postal_code' in component_type:
            location['zip'] = component['long_name']

    print(location)
    return location


def parse_addresses_from_rivers():
    """parses river geolocation data and retrieves associated address information from Google geolocation services"""
    df = pd.read_csv('data/rivers.csv').fillna('null')

    addresses = []
    # put in addresses
    for name, group in df.groupby(['put_in_lat', 'put_in_long']):
        if name[0] == 0 or name[1] == 0:
            continue

        r = requests.get('https://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s&key=%s' %
                         (name[0], name[1], settings.GEOLOCATION_API_KEY))
        components = json.loads(r.content)['results'][0]['address_components']
        addresses.append(parse_location_components(components, name[0], name[1]))

    # take out addresses
    for name, group in df.groupby(['take_out_lat', 'take_out_long']):
        if name[0] == 0 or name[1] == 0:
            continue

        r = requests.get('https://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s&key=%s' %
                         (name[0], name[1], settings.GEOLOCATION_API_KEY))

        if r.status_code == 200 and len(r.content) > 10:
            components = json.loads(r.content)['results'][0]['address_components']
            addresses.append(parse_location_components(components, name[0], name[1]))

    pd.DataFrame(addresses).to_csv('data/addresses_takeout.csv', index=False)


def scrape_snowfall():
    """scrapes daily snowfall data from NOAA"""
    base_url = 'https://www.ncdc.noaa.gov/snow-and-ice/daily-snow/WA-snow-depth-'

    snowfall = []
    for year in [2016, 2017, 2018]:
        for month in range(1, 13):
            for day in range(1, 32):
                try:
                    date = '%s%02d%02d' % (year, month, day)
                    r = requests.get(base_url + date + '.json')

                    if r.status_code == 200 and len(r.content) > 0:
                        snf = json.loads(r.content)

                        for row in snf['rows']:
                            lat = row['c'][0]['v']
                            lon = row['c'][1]['v']
                            location_name = row['c'][2]['v'].strip().lower()
                            depth = row['c'][3]['v']

                            this_row = (datetime.datetime.strptime(str(date), '%Y%m%d').date(), lat, lon, location_name, depth)
                            snowfall.append(this_row)
                            print(this_row)
                except Exception as e:
                    print([str(a) for a in e.args])

    df = pd.DataFrame(snowfall)
    df.columns = ['date', 'lat', 'lon', 'location_name', 'depth']
    df.to_csv('data/snowfall.csv', index=None)


def parse_addresses_and_stations_from_snowfall():
    """iterate through snowfall geolocation data for associated station addresses"""
    df = pd.read_csv('data/snowfall.csv')

    addresses, stations = [], []
    for name, group in df.groupby(['lat', 'lon']):
        if name[0] == 0 or name[1] == 0:
            continue

        # parse address information
        r = requests.get('https://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s&key=%s' %
                         (name[0], name[1], settings.GEOLOCATION_API_KEY))

        components = json.loads(r.content)['results'][0]['address_components']
        addresses.append(parse_location_components(components, name[0], name[1]))

        # parse station information
        station = dict()

        name = pd.unique(group.location_name)[0]
        station['station_id'] = name[name.find('(') + 1:-1].strip().lower()

        parts = name[:name.find(',')].split(' ')
        for i, s in enumerate(parts):
            if s.isdigit() or s not in \
                ['N', 'NE', 'NNE', 'ENE', 'E', 'ESE', 'SSE',
                 'SE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']:
                parts[i] = s.title()

        station['name'] = ' '.join(parts)
        station['source'] = 'NOAA'
        station['latitude'] = pd.unique(group.lat)[0]
        station['longitude'] = pd.unique(group.lon)[0]

        stations.append(station)

    pd.DataFrame(addresses).to_csv('data/addresses_snowfall.csv', index=False)
    pd.DataFrame(stations).to_csv('data/stations_snowfall.csv', index=None)


def parse_addresses_and_stations_from_precip():
    """iterate through NOAA precipitation data for associated weather station addresses"""
    stations, addresses = [], []

    for i in range(1, 16):
        path = 'data/noaa_precip/noaa_precip_%s.csv' % i
        df = pd.read_csv(path)

        for name, group in df.groupby(['STATION_NAME']):
            station = dict()

            # parse the station
            station['name'] = re.sub(r'(WA|US)', '', name).strip().title()
            station['station_id'] = re.sub(r':', '', pd.unique(group.STATION)[0]).strip().lower()
            station['source'] = 'NOAA'
            station['latitude'] = pd.unique(group.LATITUDE)[0]
            station['longitude'] = pd.unique(group.LONGITUDE)[0]

            stations.append(station)

            # parse the address
            r = requests.get('https://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s&key=%s' %
                             (station['latitude'], station['longitude'], settings.GEOLOCATION_API_KEY))

            components = json.loads(r.content)['results'][0]['address_components']
            addresses.append(
                parse_location_components(components, station['latitude'], station['longitude'])
            )

    pd.DataFrame(addresses).to_csv('data/addresses_precip.csv', index=None)
    pd.DataFrame(stations).to_csv('data/stations_precip.csv', index=None)


def get_distance_between_geo_points(lat1, lon1, lat2, lon2, run_id, station_id, source):
    """compute polar distance between two lat/long points in decimal-date (DD) format"""
    r = 6373.0

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return {
       'distance': (r * c)*0.621371,
       'station': station_id,
       'run': run_id,
       'source': source
    }


def compute_station_river_distances():
    """compute the distance from every river to every weather station"""
    repo = Repository()

    runs = repo.get_all_runs()
    stations = repo.get_all_stations()

    # foreach run, find the close USGS, NOAA, and SNOW station
    for run in runs.iterrows():
        distances = stations.apply(lambda row: get_distance_between_geo_points(
            run[1].put_in_latitude,
            run[1].put_in_longitude,
            row.latitude,
            row.longitude,
            run[1].run_id,
            row.station_id,
            row.source
        ), axis=1).apply(pd.Series)

        distances.sort_values('distance', inplace=True)

        usgs_ = distances[distances.source == 'USGS'].iloc[0, :]
        noaa_ = distances[distances.source == 'NOAA'].iloc[0, :]
        snow_ = distances[distances.source == 'SNOW'].iloc[0, :]

        usgs = StationRiverDistance(
                station_id=usgs_.station,
                run_id=run[1].run_id,
                distance=round(float(usgs_.distance), 2)
            )

        noaa = StationRiverDistance(
                station_id=noaa_.station,
                run_id=run[1].run_id,
                distance=round(float(noaa_.distance), 2)
            )

        snow = StationRiverDistance(
                station_id=snow_.station,
                run_id=run[1].run_id,
                distance=round(float(snow_.distance), 2)
            )

        repo.put_station_river_distances([usgs, noaa, snow])


def parse_addresses_and_stations_from_usgs():
    """iterate through USGS data parsing addresses from associated weather stations"""
    df = pd.read_csv('data/stations_usgs.csv').fillna('null')

    addresses, stations = [], []
    for row in df.iterrows():
        station = {
            'lat': row[1]['lat'],
            'lon': row[1]['lon'],
            'station_id': str(row[1]['site_id']).lower(),
            'name': row[1]['name'].title(),
            'source': row[1]['source']
        }
        stations.append(station)

        r = requests.get('https://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s&key=%s' %
                         (station['lat'], station['lon'], settings.GEOLOCATION_API_KEY))

        if r.status_code == 200 and len(r.content) > 10:
            components = json.loads(r.content)['results'][0]['address_components']
            addresses.append(parse_location_components(components, station['lat'], station['lon']))

    pd.DataFrame(addresses).to_csv('data/addresses_usgs.csv', index=None)
    pd.DataFrame(stations).to_csv('data/stations_usgs.csv', index=None)
