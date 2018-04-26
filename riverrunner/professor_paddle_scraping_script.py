import json
import re
import requests
import pandas as pd

GEOLOCATION_API_KEY = 'AIzaSyDPq7dNzRaVlQikArCPDTWcD57DgkUNEGE'


def scrape_rivers_urls():
    # copied from jquery selection in chrome dev tools on main prof paddle run table
    river_links = ["riverdetails.asp?riverid=4587","riverdetails.asp?riverid=344","riverdetails.asp?riverid=345","riverdetails.asp?riverid=346","riverdetails.asp?riverid=4555","riverdetails.asp?riverid=347","riverdetails.asp?riverid=4468","riverdetails.asp?riverid=348","riverdetails.asp?riverid=349","riverdetails.asp?riverid=350","riverdetails.asp?riverid=351","riverdetails.asp?riverid=352","riverdetails.asp?riverid=353","riverdetails.asp?riverid=354","riverdetails.asp?riverid=355","riverdetails.asp?riverid=356","riverdetails.asp?riverid=357","riverdetails.asp?riverid=4584","riverdetails.asp?riverid=358","riverdetails.asp?riverid=359","riverdetails.asp?riverid=360","riverdetails.asp?riverid=361","riverdetails.asp?riverid=362","riverdetails.asp?riverid=363","riverdetails.asp?riverid=364","riverdetails.asp?riverid=365","riverdetails.asp?riverid=366","riverdetails.asp?riverid=368","riverdetails.asp?riverid=4557","riverdetails.asp?riverid=4556","riverdetails.asp?riverid=367","riverdetails.asp?riverid=369","riverdetails.asp?riverid=370","riverdetails.asp?riverid=371","riverdetails.asp?riverid=372","riverdetails.asp?riverid=373","riverdetails.asp?riverid=374","riverdetails.asp?riverid=375","riverdetails.asp?riverid=376","riverdetails.asp?riverid=377","riverdetails.asp?riverid=378","riverdetails.asp?riverid=379","riverdetails.asp?riverid=380","riverdetails.asp?riverid=381","riverdetails.asp?riverid=382","riverdetails.asp?riverid=383","riverdetails.asp?riverid=384","riverdetails.asp?riverid=385","riverdetails.asp?riverid=386","riverdetails.asp?riverid=387","riverdetails.asp?riverid=388","riverdetails.asp?riverid=389","riverdetails.asp?riverid=390","riverdetails.asp?riverid=391","riverdetails.asp?riverid=392","riverdetails.asp?riverid=393","riverdetails.asp?riverid=394","riverdetails.asp?riverid=395","riverdetails.asp?riverid=396","riverdetails.asp?riverid=397","riverdetails.asp?riverid=398","riverdetails.asp?riverid=399","riverdetails.asp?riverid=400","riverdetails.asp?riverid=401","riverdetails.asp?riverid=402","riverdetails.asp?riverid=403","riverdetails.asp?riverid=404","riverdetails.asp?riverid=405","riverdetails.asp?riverid=406","riverdetails.asp?riverid=407","riverdetails.asp?riverid=408","riverdetails.asp?riverid=409","riverdetails.asp?riverid=410","riverdetails.asp?riverid=411","riverdetails.asp?riverid=412","riverdetails.asp?riverid=4566","riverdetails.asp?riverid=413","riverdetails.asp?riverid=414","riverdetails.asp?riverid=415","riverdetails.asp?riverid=416","riverdetails.asp?riverid=417","riverdetails.asp?riverid=418","riverdetails.asp?riverid=419","riverdetails.asp?riverid=420","riverdetails.asp?riverid=421","riverdetails.asp?riverid=422","riverdetails.asp?riverid=423","riverdetails.asp?riverid=424","riverdetails.asp?riverid=425","riverdetails.asp?riverid=426","riverdetails.asp?riverid=4574","riverdetails.asp?riverid=427","riverdetails.asp?riverid=428","riverdetails.asp?riverid=429","riverdetails.asp?riverid=430","riverdetails.asp?riverid=431","riverdetails.asp?riverid=432","riverdetails.asp?riverid=1037","riverdetails.asp?riverid=433","riverdetails.asp?riverid=434","riverdetails.asp?riverid=435","riverdetails.asp?riverid=1035","riverdetails.asp?riverid=436","riverdetails.asp?riverid=437","riverdetails.asp?riverid=4578","riverdetails.asp?riverid=438","riverdetails.asp?riverid=439","riverdetails.asp?riverid=440","riverdetails.asp?riverid=4583","riverdetails.asp?riverid=441","riverdetails.asp?riverid=442","riverdetails.asp?riverid=443","riverdetails.asp?riverid=444","riverdetails.asp?riverid=445","riverdetails.asp?riverid=446","riverdetails.asp?riverid=447","riverdetails.asp?riverid=448","riverdetails.asp?riverid=449","riverdetails.asp?riverid=4560","riverdetails.asp?riverid=450","riverdetails.asp?riverid=451","riverdetails.asp?riverid=452","riverdetails.asp?riverid=453","riverdetails.asp?riverid=454","riverdetails.asp?riverid=455","riverdetails.asp?riverid=456","riverdetails.asp?riverid=457","riverdetails.asp?riverid=458","riverdetails.asp?riverid=459","riverdetails.asp?riverid=460","riverdetails.asp?riverid=461","riverdetails.asp?riverid=462","riverdetails.asp?riverid=463","riverdetails.asp?riverid=464","riverdetails.asp?riverid=465","riverdetails.asp?riverid=466","riverdetails.asp?riverid=467","riverdetails.asp?riverid=1034","riverdetails.asp?riverid=468","riverdetails.asp?riverid=469","riverdetails.asp?riverid=470","riverdetails.asp?riverid=471","riverdetails.asp?riverid=472","riverdetails.asp?riverid=473","riverdetails.asp?riverid=474","riverdetails.asp?riverid=475","riverdetails.asp?riverid=476","riverdetails.asp?riverid=477","riverdetails.asp?riverid=478","riverdetails.asp?riverid=479","riverdetails.asp?riverid=480","riverdetails.asp?riverid=481","riverdetails.asp?riverid=482","riverdetails.asp?riverid=1032","riverdetails.asp?riverid=483","riverdetails.asp?riverid=484","riverdetails.asp?riverid=485","riverdetails.asp?riverid=486","riverdetails.asp?riverid=487","riverdetails.asp?riverid=488","riverdetails.asp?riverid=489","riverdetails.asp?riverid=490","riverdetails.asp?riverid=491","riverdetails.asp?riverid=4546","riverdetails.asp?riverid=492","riverdetails.asp?riverid=493","riverdetails.asp?riverid=4109","riverdetails.asp?riverid=494","riverdetails.asp?riverid=495","riverdetails.asp?riverid=496","riverdetails.asp?riverid=497","riverdetails.asp?riverid=498","riverdetails.asp?riverid=499","riverdetails.asp?riverid=500","riverdetails.asp?riverid=501","riverdetails.asp?riverid=502","riverdetails.asp?riverid=503","riverdetails.asp?riverid=4576","riverdetails.asp?riverid=504","riverdetails.asp?riverid=505","riverdetails.asp?riverid=506","riverdetails.asp?riverid=507","riverdetails.asp?riverid=508","riverdetails.asp?riverid=509","riverdetails.asp?riverid=510","riverdetails.asp?riverid=4573","riverdetails.asp?riverid=511","riverdetails.asp?riverid=512","riverdetails.asp?riverid=513","riverdetails.asp?riverid=514","riverdetails.asp?riverid=515","riverdetails.asp?riverid=516","riverdetails.asp?riverid=517","riverdetails.asp?riverid=518","riverdetails.asp?riverid=519","riverdetails.asp?riverid=520","riverdetails.asp?riverid=521","riverdetails.asp?riverid=522","riverdetails.asp?riverid=523","riverdetails.asp?riverid=524","riverdetails.asp?riverid=525","riverdetails.asp?riverid=526","riverdetails.asp?riverid=527","riverdetails.asp?riverid=528","riverdetails.asp?riverid=529","riverdetails.asp?riverid=530","riverdetails.asp?riverid=531","riverdetails.asp?riverid=532","riverdetails.asp?riverid=533","riverdetails.asp?riverid=534","riverdetails.asp?riverid=535","riverdetails.asp?riverid=536","riverdetails.asp?riverid=537","riverdetails.asp?riverid=538","riverdetails.asp?riverid=539","riverdetails.asp?riverid=4590","riverdetails.asp?riverid=540","riverdetails.asp?riverid=541","riverdetails.asp?riverid=542","riverdetails.asp?riverid=543","riverdetails.asp?riverid=544","riverdetails.asp?riverid=545","riverdetails.asp?riverid=547","riverdetails.asp?riverid=546","riverdetails.asp?riverid=548","riverdetails.asp?riverid=549","riverdetails.asp?riverid=550","riverdetails.asp?riverid=551","riverdetails.asp?riverid=552","riverdetails.asp?riverid=553","riverdetails.asp?riverid=554","riverdetails.asp?riverid=555","riverdetails.asp?riverid=556","riverdetails.asp?riverid=557","riverdetails.asp?riverid=558","riverdetails.asp?riverid=559","riverdetails.asp?riverid=560","riverdetails.asp?riverid=561","riverdetails.asp?riverid=562","riverdetails.asp?riverid=563","riverdetails.asp?riverid=564","riverdetails.asp?riverid=565","riverdetails.asp?riverid=566","riverdetails.asp?riverid=567","riverdetails.asp?riverid=568","riverdetails.asp?riverid=569","riverdetails.asp?riverid=570","riverdetails.asp?riverid=571","riverdetails.asp?riverid=572","riverdetails.asp?riverid=4579","riverdetails.asp?riverid=4580","riverdetails.asp?riverid=573","riverdetails.asp?riverid=574","riverdetails.asp?riverid=4518","riverdetails.asp?riverid=575","riverdetails.asp?riverid=4517","riverdetails.asp?riverid=576","riverdetails.asp?riverid=577","riverdetails.asp?riverid=1039","riverdetails.asp?riverid=578","riverdetails.asp?riverid=4581","riverdetails.asp?riverid=579","riverdetails.asp?riverid=580","riverdetails.asp?riverid=4572","riverdetails.asp?riverid=581","riverdetails.asp?riverid=582","riverdetails.asp?riverid=583","riverdetails.asp?riverid=584","riverdetails.asp?riverid=585","riverdetails.asp?riverid=586","riverdetails.asp?riverid=587","riverdetails.asp?riverid=588","riverdetails.asp?riverid=589","riverdetails.asp?riverid=590","riverdetails.asp?riverid=591","riverdetails.asp?riverid=592","riverdetails.asp?riverid=593","riverdetails.asp?riverid=594","riverdetails.asp?riverid=4586","riverdetails.asp?riverid=4562","riverdetails.asp?riverid=595","riverdetails.asp?riverid=4588","riverdetails.asp?riverid=596","riverdetails.asp?riverid=597","riverdetails.asp?riverid=598","riverdetails.asp?riverid=599","riverdetails.asp?riverid=600","riverdetails.asp?riverid=4585","riverdetails.asp?riverid=601","riverdetails.asp?riverid=602","riverdetails.asp?riverid=603","riverdetails.asp?riverid=4454","riverdetails.asp?riverid=4582","riverdetails.asp?riverid=4453","riverdetails.asp?riverid=4455","riverdetails.asp?riverid=604","riverdetails.asp?riverid=605","riverdetails.asp?riverid=606","riverdetails.asp?riverid=607","riverdetails.asp?riverid=608","riverdetails.asp?riverid=609","riverdetails.asp?riverid=610","riverdetails.asp?riverid=611","riverdetails.asp?riverid=612","riverdetails.asp?riverid=613","riverdetails.asp?riverid=614","riverdetails.asp?riverid=615","riverdetails.asp?riverid=616","riverdetails.asp?riverid=617","riverdetails.asp?riverid=618","riverdetails.asp?riverid=619","riverdetails.asp?riverid=620","riverdetails.asp?riverid=621","riverdetails.asp?riverid=622","riverdetails.asp?riverid=623","riverdetails.asp?riverid=624","riverdetails.asp?riverid=625","riverdetails.asp?riverid=626","riverdetails.asp?riverid=627","riverdetails.asp?riverid=628","riverdetails.asp?riverid=629","riverdetails.asp?riverid=630","riverdetails.asp?riverid=631","riverdetails.asp?riverid=632","riverdetails.asp?riverid=633","riverdetails.asp?riverid=634","riverdetails.asp?riverid=4589","riverdetails.asp?riverid=635","riverdetails.asp?riverid=636","riverdetails.asp?riverid=637","riverdetails.asp?riverid=638","riverdetails.asp?riverid=639","riverdetails.asp?riverid=4110","riverdetails.asp?riverid=640","riverdetails.asp?riverid=641","riverdetails.asp?riverid=642","riverdetails.asp?riverid=643","riverdetails.asp?riverid=644","riverdetails.asp?riverid=645","riverdetails.asp?riverid=646","riverdetails.asp?riverid=647","riverdetails.asp?riverid=648","riverdetails.asp?riverid=649","riverdetails.asp?riverid=650","riverdetails.asp?riverid=651","riverdetails.asp?riverid=654","riverdetails.asp?riverid=652","riverdetails.asp?riverid=655","riverdetails.asp?riverid=656","riverdetails.asp?riverid=657","riverdetails.asp?riverid=658","riverdetails.asp?riverid=1036","riverdetails.asp?riverid=653","riverdetails.asp?riverid=659","riverdetails.asp?riverid=660","riverdetails.asp?riverid=661","riverdetails.asp?riverid=662","riverdetails.asp?riverid=663","riverdetails.asp?riverid=664","riverdetails.asp?riverid=665","riverdetails.asp?riverid=666","riverdetails.asp?riverid=667","riverdetails.asp?riverid=1038","riverdetails.asp?riverid=668","riverdetails.asp?riverid=669","riverdetails.asp?riverid=670","riverdetails.asp?riverid=671","riverdetails.asp?riverid=672","riverdetails.asp?riverid=673","riverdetails.asp?riverid=674","riverdetails.asp?riverid=675","riverdetails.asp?riverid=676","riverdetails.asp?riverid=677","riverdetails.asp?riverid=678","riverdetails.asp?riverid=679","riverdetails.asp?riverid=680","riverdetails.asp?riverid=681","riverdetails.asp?riverid=682","riverdetails.asp?riverid=683","riverdetails.asp?riverid=684","riverdetails.asp?riverid=685","riverdetails.asp?riverid=686"]

    river_ids = [r[r.find("=")+1:] for r in river_links]
    url = "http://www.professorpaddle.com/rivers/riverdetails.asp?riverid="

    # for id in river_ids:
    #     r = req.get(url + id)
    #
    #     if r.status_code == 200:
    #         with open("river_%s.html" % id, 'w+') as f:
    #             f.write(str(r.content))

    rivers = []
    for rid in river_ids:
        with open(('C:\\Users\\lukew\\OneDrive\\School\\river_pages\\river_%s.html') % rid) as f:
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
        row['run_name'] = run_name
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


def remove_white_extra_white_space_from_run_names():
    df = pd.read_csv('rivers2.csv')

    df.run_name = [re.sub(r'(  )+', ' ', run) for run in df.run_name]

    df.to_csv('data/rivers2.csv')


def fill_river_location_data():
    df = pd.read_csv('data/rivers2.csv').fillna('null')

    addresses = []
    for name, group in df.groupby(['put_in_lat', 'put_in_long']):
        if name[0] == 0 or name[1] == 0:
            continue

        r = requests.get('https://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s&key=%s' %
                         (name[0], name[1], GEOLOCATION_API_KEY))
        components = json.loads(r.content)['results'][0]['address_components']

        location = {}
        for component in components:
            location['latitude'] = name[0]
            location['longitude'] = name[1]

            type = component['types']

            if 'route' in type:
                location['address'] = component['long_name']
            elif 'locality' in type:
                location['city'] = component['long_name']
            elif 'administrative_area_level_2' in type:
                location['route'] = component['long_name']
            elif 'administrative_area_level_1' in type:
                location['state'] = component['short_name']
            elif 'postal_code' in type:
                location['zip'] = component['long_name']
        addresses.append(location)

    pd.DataFrame(addresses).to_csv('data/locations.csv', index=False)
