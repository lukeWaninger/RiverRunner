# Design Specification

## Overview
The following diagram shows the high level design of River Runner:

![Design mockup](design.png)

Detailed specifications for each component are described below.

## Components

### Retrieve Historical Data
Historical data was retrieved via single use Python scripts that scrape, process, and commit historical data to the database described in this document. The main modules being used for this are `json`, `re`, `requests`, and `pandas`.

#### River/Run Information
The runs being processed by this application are static and were gathered at the time of initial development. Each run was retrieved from <a alt='Professor Paddle' href='http://www.professorpaddle.com'>Professor Paddle </a>. Initial river IDs are pulled from Professor Paddle's main page with Chrome dev tools and JQuery. URLs are then generated for each river and retrieved via `requests` and processed character-by-character into a Pandas data frame and saved to '/data/rivers.csv'. `def scrape_river_urls()`

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

Associated address information is processed in `def parse_addresses_from_rivers()`.

#### NOAA Temperature/Precipitation Data
Temperature and precipitation data was gathered through individual requests for each station on the NOAA website. Each request returned a CSV file with all recording for the specific weather station. Addresses and stations were parsed from these files in `def parse_addresses_and_stations_from_precip()`.

#### NOAA Snowpack Data
Initial snowpack data was retrieved from <a alt='NOAA snowpack' href='https://www.ncdc.noaa.gov/snow-and-ice/daily-snow/'>NOAA</a>.
The function `def scrape_snowfall()` retrieves snowpack data for all reporting stations in Washington, one day at a 
time. Results are saved to 'data/snowfall.csv' and manually uploaded to the database.

<b>relational mapping</b> - stored to <i>metric</i>, <i>station</i>, and <i>measurement</i>  
gathered attributes are
* date: <em>timestamp</em> - timestamp measurement was recorded
* lat:  <em>real</em> - geographical latitude of reporting station
* lon:  <em>real</em> - geographical longitude of reporting station
* location_name: <em>varchar(31)</em> - name of reporting station
* depth: <em>real</em> - recorded depth of snow measured in inches

Addresses and stations associated with each measurement are processed from their respective latitude and longitudes through `def parse_addresses_and_stations_from_snowfal()` and saved to the csv file described above.

#### Location Data
Address information is retrieved using `requests` through Google's <a alt='Google Geocoding' href='https://developers.google.com/maps/documentation/geocoding/start'>Geocoding API</a>. Each latitude and longitude pair throughout the application is processed through the API in order to retrieve related political boundary information. JSON results are processed through  `def parse_location_components()` and inserted into the database.

<b>relational mapping</b>
<b>state</b> - <i>state indentification information</i>    
* short_name: <em>varchar(2)</em> -  two letter state indicator code, PK
* long_name: <em>varchar(31)</em> - state’s full spelling    

<b>address</b> - <i>political boundary data related to GPS locations</i>     
* latitude: <em>real</em> - GPS position in decimal degree (DD) formatting, PK
* longitude: <em>real</em> - GPS position in decimal degree (DD) formatting, PK
* city: <em>varchar(255)</em> - name of closest city
* county: <em>varchar(255)</em> - name of county
* state: <em>varchar(2)</em> - two letter state identification code, FK->[state].short_name
* address: <em>varchar(255)</em> - closest street address to point
* zip: <em>varchar(10)</em> - zip code

#### USGS Streamflow Data
To collect streamflow data for all river runs we retrieved a list of all <a href='https://waterdata.usgs.gov/wa/nwis/uv'>USGS stream sites</a> (stations) in the state of Washington. Using this list and python's `requests` module, the retrieval process is outlined below:

* Call USGS's Instantaneous Values API for each combination of site and metric, returning data in a JSON format
* Extract timestamp and measurement value from JSON format and write to CSV file
* Insert records in CSV file into the database

<b>relational mapping</b> - <i>measurement</i>
* site_id: <em>varchar(31)</em> - id of site taken directly from list of all USGS stream sites
* metric_id: <em>varchar(31)</em> - id of metric taken directly from list of all USGS metrics
* date_time: <em>timestamp</em> - timestamp when measurement was recorded
* value: <em>real</em> - recorded measurement

### Continuous Data Retrieval
Retrieving all static and historical data need only be done once, but to keep the data up to date we need to continuously retrieve and integrate all new time series data into the database. The following data is retrieved on a daily basis.

#### DarkSky Temperature/Precipitation Data
Since retrieving historical temperature and precipitation data from NOAA involves sending a request and receiving an email in response containing a link to download the requested data (a process that would be cumbersome to repeat on a daily basis), <a href='https://darksky.net/dev'>DarkSky</a> (DarkSky), which provided simpler automatability was used for ongoing temperature and precipitation data. Continuous API calls to DarkSky are made with the `continuous.py` module.

#### USGS Streamflow Data
<a href='https://waterservices.usgs.gov/rest/IV-Test-Tool.html'>USGS's Instantaneous Values API</a> makes it easy to automate the continuous retrieval of time series data. Repeated calls to the USGS Instantaneous Values REST web service are also made using the `continuous.py` module.

#### Snowpack Data
Snowpack is not currently being used as an exogenous predictor in our models, so it is not being collected on an ongoing basis at this time. However, as part of the process of retrieving historical snowpack data, we retrieved time series data from this source one day at a time. So, the `scrape_snowfall()` function could seemlessly be reused to continuously retrieve new data in the future, with the only modification needed is to automate the uploading of snowpack data into the database.

### RDBMS
All data is gathered and processed according to this specification before being committed for persistence. Persistence is managed through an RDBMS - PostgresSQL 10.3 - Ubuntu Server 16.04 LTE.
</br>
![RiverRunner schema](schema.png)
<br/>
Each table listed below indices on it's primary key unless otherwise noted.

<b>station</b> - <i>weather reporting stations for both NOAA and USGS data points</i>    
* station_id <em>varchar(31)</em>: the station id for the weather station as listed by the station's data , PK
* source <em>varchar(4)</em> the original data source author
* name <em>varach(255)</em> the human readable statin name as listed by original data source
* latitude <em>real</em> station's geographical latitude (DD), FK->[addresses].latitude
* longitude <em>real</em> station's geographical longitude (DD), FK->[addresses].longitude

<i>indices</i>
+ clustered index on (latitude, longitude)
+ unclustered index on (station_id) 

<b>station_river_distance</b> - <i>stores geographical distances between each run and each weather station.</i> 
* station_id <em>varchar(31)</em>: station for which distance is computed, PK, FK->[station].station_id
* run_id <em>integer</em>: river for which distance is computed, PK, FK->[river_run].river_id  
* distance <em>real</em>: distance measured in miles from run's starting point to weather station

<i>indices</i>
+ clustered index on (put_in_distance)
+ unclustered index on (station_id, river_id)

Distances are calculated via the following code snippet
```python
    a = sin((lat2-lat1)/2)**2 + cos(lat1) * cos(lat2) * sin((lon2-lon1)/2)**2
    c = 2*atan2(sqrt(a), sqrt(1 - a))

    return r*c*0.621371
```

<b>metric</b> - <i>stores all the metric types that will be used for prediction</i>     
* metric_id <em>varchar(31)</em>: the metric's id as listed by original data source, PK
* name <em>varchar(31)</em>: the metric's human readable name as listed by original data source
* description <em>varchar(255)</em>: brief description of the metric
* units <em>varchar(31)</em>: units for which the metric is recorded in

<b>measurement</b> - <i>stores all gathered measurements from each weather station</i>     
* station_id <em>varchar(31)</em> id of weather station for which the measurement was recorded, PK, FK->[station].station_id
* metric_id <em>varchar(31)</em> id of associated metric being measured, PK, FK->[metric].metric_id
* date_time <em>timestamp</em> timestamp for when the measurement was recorded, PK
* value <em>real</em> the measurement value recorded

<i>indices</i>
+ clustered index on (date_time)
+ unclustered index on (station_id), (metric_id)

<b>river_run</b> - <i>stores static river run information</i>     
* run_id <em>integer</em> unique identifier for river run, PK
* class_rating <em>varchar(31)</em> class rating (difficulty) for the river run
* max_level <em>integer</em> maximum runnable flow rate
* min_level <em>integer</em> minimum runnable flow rate
* put_in_latitude <em>real</em> latitude of put in location
* put_in_longitude <em>real</em> longitude of put in location
* distance <em>real</em> distance between put in and take out locations
* river_name <em>varchar(255)</em> name of the river that run is on
* run_name <em>varchar(255)</em> run name
* take_out_latitude <em>real</em> latitude of take out location
* take_out_longitude <em>real</em> longitude of take out location


<b>prediction</b> - <i>stores predicted flow rates for each run as generated by ARIMA model</i>     
* run_id <em>integer</em> run for which predictions were generated, PK, FK->[river_run].run_id
* timestamp <em>timestamp</em> date for which prediction was generated, PK
* fr_lb <em>double precision</em> lower error bound of flow rate prediction
* fr <em>double precision</em> predicted flow rate
* fr_ub <em>double precision</em> upper error bound of flow rate prediction

### Object Relational Mapping
ORM is being used to map our Python classes to the database backend. We elected to use `sqlalchemy` for this as it 
gives us more flexibility with hybrid properties and other joining methods. All tables described in the RDMS section above have associated Python classes. This keeps our model fluid and allows easier DB installation through `sqlalchemy`'s `create_all()` method.

### Server Side Predictions
Future river flow rates are predicted using an autoregressive integrated moving average (ARIMA) model generated from historic USGS river flow rate time series data. Temperature and precipitation are included in the models as exogenous predictor variables; snowpack will be included as an exogenous predictor at a later date if deemed useful, but was not used for the first release. Models are generated using the past four years of historical data up to the current day, and predictions are made for the future seven days.

Exploration of the data was completed using `arima_exploration.py`. The `test_stationarity()` function was used to determine that flow rate is non-stationary on a short timeframe due to annual seasonality but stationary over longer periods of time; since most variation is caused short-term spikes in flow rate, this is averaged out over longer periods. Due to the large difference between the seasonality timeframe (annual) and the prediction timeframe (daily), the best models with the highest probability of convergence resulted from using an ARMA model (no differencing) on several years worth of stationary data for the run. The optimal order of the ARMA model for each run (i.e. p and q parameters) was examined for a few test runs using `plot_autocorrs()` to generate autocorrelation and partial autocorrelation plots for lag order and moving average order respectively. Since this analysis must be done manually, the order of ongoing models is determined using built-in python functions.

The module `arima.py` is used to build and fit the flow rate models for a given river run. The `get_data()` function retrieves data for a selected run from the database for past four years from the current date using `Repository.get_measurements()` function. Feature engineering to create daily averages of all predictor variables is completed using the `daily_avg()` function. The `arima_model()` function is used to create the model for the given run. ARIMA model orders for each run are determined each time using the python statsmodels.tsa.stattools package's arma_order_select_ic function using AIC penalized likelihood criteria. These results are then fed along with the data into the python statsmodels.tsa.arima_model package's ARIMA function to build the model. Finally, the model .forecast function is used to generate predictions for the next seven days. In case of non-convergence at either the order determination or model fitting, `arima_model()` will return the last known flow rate value applied to the next seven days. 

Immediately following daily data retrieval, the ARIMA models are recalculated for each run with the results stored in a dataframe for plotting.

### Dash Client Side Interface
The front end user interface is a simple web based UI implemented by the `ui.py` module. The UI is built using Dash, and consists of:
 - A dropdown menu with searching capabilities for river run selection 
 - A plot for the selected river run containing:
    - 21 days of historic flow rate
    - 7 days of future predicted flow rate
    - A highlighted band showing the maximum and minimum runnable levels for the run
 - A map of all put in locations, color coded by runnability status

Basic interactivity is also implemented with Dash, including a popup with flow rate details upon hover for the plot, and selection of river run using the dropdown or the map.

## Interactions
### Use Case 1: The Paddler
The paddler requests to view stream flow predictions for a specific kayaking run. The user has two options for finding a river's flow rate predictions:
1. User searches for a river by typing the river name in the top search bar. The bar will autopopulate with a drop down to filter run names as the user types. Selecting a run will request a prediction.
2. User views the runs populated on the map, clicking a point to retrieve predictions.

The page will have loaded with a .csv file containing predictions for the following two weeks. Using javascript, the prediction image will redraw with the selected run's prediction.
