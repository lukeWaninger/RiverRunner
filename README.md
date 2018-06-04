<a href="http://lkwaninger.ddns.net:8111/viewType.html?buildTypeId=RiverRunner_Build&guest=1">
<img align="right" src="http://lkwaninger.ddns.net:8111/app/rest/builds/buildType:(id:RiverRunner_Build)/statusIcon"/>
</a>

<img src=https://github.com/kentdanas/RiverRunner/raw/master/doc/logo.png  width="200" height="200" />

# River Runner
River Runner is a simple web-based tool that allows whitewater kayakers to see flow rate predictions for river runs in Washington state in order to help plan future kayaking trips. By using autoregressive integrated moving average (ARIMA) models on public USGS historical river flow rate data, along with exogenous regressors such as precipitation, snow pack, and temperature, River Runner provides predictions of daily average river flow rates seven days in advance. Results are shown on a plot along with the maximum and minimum runnable flow rates so paddlers can easily see whether the river is predicted to be runnable.

## Project Organization
Our project has the following structure:
```
RiverRunner/
  |- doc/
     |- continuous_retrieval/
        |- index.rst
     |- data_abstraction/
        |- index.rst
     |- design_specification/  
        |- design.png
        |- DesignSpecification.md
        |- schema.png
     |- functional_specification/  
        |- FunctionalSpecification.md
        |- mockup.png
     |- prediction/
        |- index.rst
     |- repository/
        |- index.rst
     |- Makefile
     |- conf.py
     |- index.rst
     |- logo.png
     |- make.bat
     |- RiverRunner_final_presentation.pdf
  |- examples/
  |- riverrunner/
     |- tests/
        |- __init__.py
        |- arima_tests.py
        |- context_tests.py
        |- data_retrieval_tests.py
        |- repository_tests.py
        |- tcontext.py
     |- __init__.py
     |- arima.py
     |- arima_exploration.py
     |- context.py
     |- continuous_retrieval.py
     |- daily.py
     |- repository.py
     |- static_data_scraping_functions.py
     |- ui.py
  |- .coverageerc
  |- .gitignore
  |- LICENSE
  |- README.md
  |- requirements.txt
```

## Examples
A demo video of interacting with the River Runner UI to access predictions can be found on the [examples](https://github.com/kentdanas/RiverRunner/tree/master/examples) section of this GitHub page.

## Project History
The idea for River Runner was developed in April 2018 for the University of Washington's DATA 515 Software Engineering for Data Scientists course by Kenten Danas, Luke Waninger, and Ryan Bald. Having whitewater kayaked in Washington for several years, Kenten recognized the potential of a tool that could predict the flow rate of a given river run up to a few weeks in advance to help with planning weekend kayaking trips. The first objective we set was to create a preliminary ARIMA model that could be used to predict river run flow rates. We then created a basic ui from which paddlers can select a river run either from a dropdown or a map to see the predictions.

Going forward, we hope to expand the scope of the project to include more river runs. We also hope to further refine the models used to improve accuracy and extend the forecasted flow rates beyond seven days.  

## Limitations
The scope of River Runner is currently limited to whitewater kayaking runs in Washington State. Some runs in Washington may not be available for predictions due to lack of flow rate data from the closest USGS station.  

## Acknowledgements
We extend thanks to our University of Washington DATA 515 professors, Joe Hellerstein and Dave Beck, for providing guidance throughout this project on software engineering best practices.

Resources used to collect the data needed for this project include [Professor Paddle](http://www.professorpaddle.com/rivers/riverlist.asp), NOAA, USGS, and DarkSky.
