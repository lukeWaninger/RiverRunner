import datetime
import json
import requests
import pandas as pd

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
                        location_name = row['c'][2]['v']
                        depth = row['c'][3]['v']

                        this_row = (datetime.datetime.strptime(str(date), '%Y%m%d').date(), lat, lon, location_name, depth)
                        snowfall.append(this_row)
                        print(this_row)
            except Exception as e:
                print([str(a) for a in e.args])

df = pd.DataFrame(snowfall)
df.columns = ['date', 'lat', 'lon', 'location_name', 'depth']
df.to_csv('data/snowfall.csv', index=None)



