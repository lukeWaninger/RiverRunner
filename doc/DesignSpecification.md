# River Runner - Design Specification

## Components

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
