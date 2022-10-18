
from pandas import Categorical, DataFrame
import plotnine as gg
from random import randrange

# Create dataframe
dataframe = DataFrame(data = {"column1": list(range(10)), 
								 "column2": list(range(10)),
								 "column3": [0, 1] * 5,
								 "column4": [randrange(start=0, stop=10) for _ in range(10)]})
dataframe["column3"] = Categorical(dataframe.column3)

plot = gg.ggplot(dataframe, gg.aes(x="column1", y="column2", colour="column3")) \
	+ gg.geom_point(size=2) \
	+ gg.geom_line(gg.aes(y="column4"), colour="green", size=1.5) \
    + gg.scale_colour_manual(values=["blue", "red"], guide=False) \
	+ gg.theme_light() \
	+ gg.theme(figure_size=(10, 5), 
			   text=gg.element_text(size=12))

print(dataframe)
# print(plot)

from strava.plotting.strava_stream_plots import PlotTheme

pt = PlotTheme()
pt.dark()

print(plot + pt.gg_theme())