# Functional Specification

## Background

Whitewater kayaking is a popular sport around Washington state where there are many runnable rivers within a short drive from urban areas. What draws many people to the sport is its dynamic nature; it is fast paced and intense, and even running the same stretch of river can be a totally different experience each time depending on the flow conditions. Many river's flow rates change quickly and dramatically, meaning paddlers must be ready to adapt to rapidly changing conditions and able to determine whether a river is runnable. A river that may be an easy class III today might be a more difficult class IV or entirely unrunnable tomorrow.

For many sports that are weather-dependent, modern day weather forcasting provides relatively accurate predictions of conditions up to ten days in advance making it relatively easy to plan ahead for any outdoor activities. For whitewater kayaking however, there are currently no reliable tools which can predict a river's flow rate, meaning paddlers are often left to figure out whether they can run a given river less than a day in advance or even the morning of their planned trip. Especially for newer paddlers who have fewer choices of rivers to run, or paddlers who have to plan ahead for traveling longer distances to get to the river, this can lead to many cancelled trips and dissapointing weekends without paddling. Being able to get a sense of what rivers might be runnable further than a day or two in advance would undoubtedly help many paddlers get the most of their time on the river. 

With RiverRunner, the goal is to provide paddlers in Washington<sup>1</sup> with a simple web-based tool that will allow them to see a prediction of a given river run's flow rate in order to help plan future kayaking trips. By using autoregressive integrated moving average (ARIMA) models on public USGS historical river flow rate data, along with exogenous regressors such as precipitation, snow pack, and temperature, we hope to provide accurate predictions of daily average river flow rates up to two weeks in advance. The tool will be relatively simple to create and maintain, easy to use, and will provide a clear benefit to the whitewater community in Washington State.

<sub><sup>1</sup>The current scope of the RiverRunner project only includes predictions for whitewater runs in Washington State. Depending on the success of the models and demand, this could potentially be expanded to include rivers in other states in the future.</sub>

## Users

The target users of RiverRunner are individuals who whitewater kayak in Washington state and would benefit from knowing in advance whether a river will be runnable. This could include recreational paddlers, professional paddlers, kayaking competition organizers, and kayaking companies. 

For all of these users, the computer experience required to use the tool is general familiarity with operating simple web-based graphical user interfaces. The domain knowledge required is familiarity with the sport and the impact of river flow levels on paddling conditions. Users will need to understand what it means for a river to be within its stated runnable flow range, as well as how conditions could vary given a certain margin of error in the predicted flow rate. 

## Use Cases

Paddlers will use RiverRunner to help plan their kayaking trips by getting a prediction of a selected river's daily average flow rate up to two weeks in advance, which will provide an indication of whether the river will be runnable. The user will access the tool through a webpage, and select a river run by name from a drop-down filter. The system will respond with a plot of that run's historic flow rate for the past four weeks along with the flow rate predicted by the model, which will extend up to two weeks into the future. The plot will include a highlighted band between the maximum and minimum runnable flows for the selected run (where available) so the user can easily identify whether the predicted flow rate falls in the desired range. The tool will also include a map which will update based on the selected river run to show the put-in and take-out locations.

## Mockup

The picture below shows a rough mockup of the planned RiverRunner user interface:

![RiverRunner mockup](mockup.png)
