# River Runner - Design Specification

## Components

### Database
PostgresSQL 10.3 - Ubuntu Server 16.04 LTE
</br>
<img src="https://raw.githubusercontent.com/kentdanas/RiverRunner/master/doc/schema.png" width=400 style='display:block; margin-left:auto; margin-right:auto'>
<br/>
#### Tables
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

* <b>river_run</b> - <i>white water rafting sites and related information </i>   
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
<br/>

* <b>station</b> - <i>weather reporting stations for both NOAA and USGS data points</i>     
<em></em>: <em></em>

* <b>station_river_distance</b> - <i></em>     
<em></em>: <em></em>

* <b>metric</b> - <i></i>     
<em></em>: <em></em>

* <b>measurement</b> - <i></i>     
<em></em>: <em></em>  

### Retrieve Historical Data

#### River/Run Information

#### Temperature/Precipitation Data

#### Snowfall Data

#### River Metric Data

For all rivers in Washington, we would like to have time series data for streamflow and a wide variety of other metrics to use as predictors for streamflow. We first retrieve a list of all USGS stream sites (stations) in the state of Washington and formulate a list of all metrics (that are provided by USGS) we would like to include in our model as predictors. Using these lists and python's `requests` module, the retrieval process is outlined below:

* Call USGS's Instantaneous Values API for each combination of site and metric, returning data in a JSON format
* Extract timestamp and measurement value from JSON format and write to CSV file
* Insert records in CSV file to our database storage

### Continuous Data Retrieval

#### Temperature/Precipitation Data

#### Snowfall Data

#### River Metric Data

## Interactions
