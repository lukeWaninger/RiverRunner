# River Runner - Design Specification

## Components

### Database
PostgresSQL 10.3 - Ubuntu Server 16.04 LTE
<img src="https://raw.githubusercontent.com/kentdanas/RiverRunner/master/doc/schema.png" width=400 style='display:block; margin-left:auto; margin-right:auto'>

#### Tables
Each table listed below indices on it's primary key unless otherwise noted
* <strong>state</strong> - <span style='font-style:italic'>state indentification information</span>     
  <span style='text-decoration:underline'>short_name</span>: <span style='color:darkblue'>varchar(2)</span> -  two letter state indicator code, PK
  long_name: <span style='color:darkblue'>varchar(31)</span> - state’s full spelling    
<br/>

* <strong>address</strong> - <span style='font-style:italic'>political boundary data related to GPS locations</span>     
  <span style='text-decoration:underline'>latitude</span>: <span style='color:darkblue'>real</span> - GPS position in decimal degree (DD) formatting, PK
  <span style='text-decoration:underline'>longitude</span>: <span style='color:darkblue'>real</span> - GPS position in decimal degree (DD) formatting, PK
  city: <span style='color:darkblue'>varchar(255)</span> - name of closest city
  county: <span style='color:darkblue'>varchar(255)</span> - name of county
  state: <span style='color:darkblue'>varchar(2)</span> - two letter state identification code, FK$\rightarrow$[state].short_name
  address: <span style='color:darkblue'>varchar(255)</span> - closest street address to point
  zip: <span style='color:darkblue'>varchar(10)</span> - zip code
<br/>

* <strong>river_run</strong> - <span style='font-style:italic'>white water rafting sites and related information </span>
  <span style='text-decoration:underline'>river_id</span>: <span style='color:darkblue'>integer</span> PK as pulled  from <a alt='Professor Paddle' href='http://www.professorpaddle.com'>Professor Paddle </a>
  class_rating: <span style='color:darkblue'>varchar(31)</span> - white water rating
  max_level: <span style='color:darkblue'>integer</span> - maximum recommended stream flow for run
  min_level: <span style='color:darkblue'>integer</span> - minimum recommended stream flow for run
  put_in_latitude: <span style='color:darkblue'>real</span> - run starting point latitude (DD), FK$\rightarrow$[addresses].latitude
  put_in_longitude: <span style='color:darkblue'>real</span> - run starting point longitude (DD), FK$\rightarrow$[addresses].longitude
  distance: <span style='color:darkblue'>real</span> - run length
  river_name: <span style='color:darkblue'>varchar(255)</span> - name of river
  run_name: <span style='color:darkblue'>varchar(255)</span> - name of run
  take_out_latitude: <span style='color:darkblue'>real</span> - run ending point latitude (DD), FK$\rightarrow$[addresses].latitude
  take_out_longitude: <span style='color:darkblue'>real</span> - run ending point longitude (DD), FK$\rightarrow$[addresses].longitude
<br/>

* <strong>station</strong> - <span style='font-style:italic'>weather reporting stations for both NOAA and USGS data points</span>     
<span style='text-decoration:underline'></span>: <span style='color:darkblue'></span>

* <strong>station_river_distance</strong> - <span style='font-style:italic'></span>     
<span style='text-decoration:underline'></span>: <span style='color:darkblue'></span>

* <strong>metric</strong> - <span style='font-style:italic'></span>     
<span style='text-decoration:underline'></span>: <span style='color:darkblue'></span>

* <strong>measurement</strong> - <span style='font-style:italic'></span>     
<span style='text-decoration:underline'></span>: <span style='color:darkblue'></span>
=======
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

>>>>>>> 17112ff7367483da8a668b1a1dbccf8b4e3dcba4
## Interactions
