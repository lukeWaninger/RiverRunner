# River Runner - Design Specification

## Components

### Retrieve Historical Data
Historical data will be retrieved via single use Python scripts that scrape, process, and commit historical data to the 
database described in this document.
The main modules being used for this will be `json`, `re`, `requests`, and `pandas`.

#### River/Run Information
The runs being processed by this application are static and gathered at the time of initial development. Each run is 
retrieved from <a alt='Professor Paddle' href='http://www.professorpaddle.com'>Professor Paddle </a>
Initial river IDs are pulled from Professor Paddle's main page with Chrome dev tools and JQuery. URLs are then 
generated for each river and retrieved via `requests` and processed character-by-character into a Pandas data frame 
and saved to '/data/rivers.csv'. 
`def scrape_river_urls()`  

<b>relational mapping</b> - <i>river_run</i>  
* <em>river_id</em>: <em>integer</em> PK as pulled  from <a alt='Professor Paddle' href='http://www.professorpaddle.com'>Professor Paddle </a>
* class_rating: <em>varchar(31)</em> - white water rating
* max_level: <em>integer</em> - maximum recommended stream flow for run
* min_level: <em>integer</em> - minimum recommended stream flow for run
* put_in_latitude: <em>real</em> - run starting point latitude (DD), FK->[addresses].latitude
* put_in_longitude: <em>real</em> - run starting point longitude (DD), FK->[addresses].longitude
* distance: <em>real</em> - run length
* river_name: <em>varchar(255)</em> - name of river
* run_name: <em>varchar(255)</em> - name of run
* take_out_latitude: <em>real</em> - run ending point latitude (DD), FK->[addresses].latitude
* take_out_longitude: <em>real</em> - run ending point longitude (DD), FK->[addresses].longitude

Associated address information is process in `def parse_addresses_from_rivers()`.

#### Temperature/Precipitation Data
Temperature and precipitation data was gathered through individual requests for each station on the NOAA website. 
Each request returned a CSV file with all recording for the specific weather station. Addresses and stations were 
parsed from these files in `def parse_addresses_and_stations_from_precip()`.

#### Snowfall Data
Initial snowfall data was retrieved from <a alt='NOAA snowfall' href='https://www.ncdc.noaa.gov/snow-and-ice/daily-snow/'>NOAA</a>
The function `def scrape_snowfall()` retrieves snowfall data for all reporting stations in Washington, one day at a 
time. Results are saved to 'data/snowfall.csv' and manually uploaded to the database.

<b>relational mapping</b> - stored to <i>metric</i>, <i>station</i>, and <i>measurement</i>  
gathered attributes are
* date: <em>timestamp</em> - timestamp measurement was recorded
* lat:  <em>real</em> - geographical latitude of reporting station
* lon:  <em>real</em> - geographical longitude of reporting station
* location_name <em>varchar(31)</em> - name of reporting station
* depth: <em>real</em> - recorded depth of snow measured in inches

Addresses and stations associated with each measurement are processed from their respective latitude and longitudes 
through `def parse_addresses_and_stations_from_snowfal()` and saved to the csv file described above.

#### Location Data
Address information is retrieved using `requests` through Google's <a alt='Google Geocoding' href='https://developers.google.com/maps/documentation/geocoding/start'>Geocoding API</a> 
Each latitude and longitude pair throughout the application is processed through the API in order to retrieve related
 political boundary information. JSON results are processed through  `def parse_location_components()` and inserted 
 into the database.
 
 <b>relational mapping</b> - <i>address</i>, <i>state</i>
 * latitude: <em>real</em> - geographical latitude (DD), PK
 * longitude: <em>real</em> - geographical longitude (DD), PK
 * address: <em>varchar(255)</em> - street address
 * city: <em>varchar(255)</em> - city
 * state: <em>varchar(2)</em> - 2 letter state identification code, FK->[state].state_id
 * zip: <em>varchar(10)</em> - up to ten character zip code  

#### River Metric Data

For all rivers in Washington, we would like to have time series data for streamflow and a wide variety of other metrics to use as predictors for streamflow. We first retrieve a list of all USGS stream sites (stations) in the state of Washington and formulate a list of all metrics (that are provided by USGS) we would like to include in our model as predictors. Using these lists and python's `requests` module, the retrieval process is outlined below:

* Call USGS's Instantaneous Values API for each combination of site and metric, returning data in a JSON format
* Extract timestamp and measurement value from JSON format and write to CSV file
* Insert records in CSV file to our database storage

#### Additional schema information
All data will be gathered and processed according to this specification before being committed for persistence. Persistence will be managed through an RDBMS - PostgresSQL 10.3 - Ubuntu Server 16.04 LTE.
</br>
<img src="https://raw.githubusercontent.com/kentdanas/RiverRunner/master/doc/schema.png" width=400 style='display:block; margin-left:auto; margin-right:auto'>
<br/>
Each table listed below indices on it's primary key unless otherwise noted
* <b>state</b> - <i>state indentification information</i>    
    * short_name: <em>varchar(2)</em> -  two letter state indicator code, PK
    * long_name: <em>varchar(31)</em> - state’s full spelling    
<br/>

* <b>address</b> - <i>political boundary data related to GPS locations</i>     
    * latitude: <em>real</em> - GPS position in decimal degree (DD) formatting, PK
    * longitude: <em>real</em> - GPS position in decimal degree (DD) formatting, PK
    * city: <em>varchar(255)</em> - name of closest city
    * county: <em>varchar(255)</em> - name of county
    * state: <em>varchar(2)</em> - two letter state identification code, FK->[state].short_name
    * address: <em>varchar(255)</em> - closest street address to point
    * zip: <em>varchar(10)</em> - zip code
<br/>

* <b>station</b> - <i>weather reporting stations for both NOAA and USGS data points</i>    
   * station_id <em>varchar(31)</em>: the station id for the weather station as listed by the station's data , PK
   * source <em>varchar(4)</em> the original data source author
   * name <em>varach(255)</em> the human readable statin name as listed by original data source
   * latitude <em>real</em> station's geographical latitude (DD), FK->[addresses].latitude
   * longitude <em>real</em> station's geographical longitude (DD), FK->[addresses].longitude
   + clustered index on (latitude, longitude)
   + unclustered index on (station_id) 

* <b>station_river_distance</b> - <i>stores geographical distances between each run and each weather station.</i> 
    * station_id <em>varchar(31)</em>: station for which distance is computed, PK, FK->[station].station_id
    * river_id <em>integer</em>: river for which distance is computed, PK, FK->[river_run].river_id  
    * put_in_distance <em>real</em>: distance measured in miles from run's starting point to weather station
    * tak_out_distance <em>real</em>: distance measured in miles from run's ending point to weather station
    + clustered index on (put_in_distance)
    + unclustered index on (station_id, river_id)

Distances are calculated via the following code snippet
```python
    a = sin((lat2-lat1)/2)**2 + cos(lat1) * cos(lat2) * sin((lon2-lon1)/2)**2
    c = 2*atan2(sqrt(a), sqrt(1 - a))

    return r*c*0.621371
```

* <b>metric</b> - <i>stores all the metric types that will be used for prediction</i>     
    * metric_id <em>varchar(31)</em>: the metric's id as listed by original data source, PK
    * name <em>varchar(31)</em>: the metric's human readable name as listed by original data source
    * description <em>varchar(255)</em>: brief description of the metric
    * units <em>varchar(31)</em>: units for which the metric is recorded in

* <b>measurement</b> - <i>stores all gathered measurements from each weather station</i>     
    * station_id <em>varchar(31)</em> id of weather station for which the measurement was recorded, PK, FK->[station].station_id
    * metric_id <em>varchar(31)</em> id of associated metric being measured, PK, FK->[metric].metric_id
    * date_time <em>timestamp</em> timestamp for when the measurement was recorded, PK
    * value <em>real</em> the measurement value recorded
    + clustered index on (date_time)
    + unclustered index on (station_id), (metric_id)

### Continuous Data Retrieval

#### Temperature/Precipitation Data

#### Snowfall Data

#### River Metric Data

## Interactions