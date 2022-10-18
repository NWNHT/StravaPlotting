# Contains functions to create plots summarizing activities over multliple years

from .strava_stream_plots import *

import datetime
import pandas as pd
from plotnine import ggplot, aes
import plotnine as gg


# Create special theme elements for annual plots
annual_theme = gg.theme(axis_text_x=gg.element_text(size=16), axis_text_y=gg.element_text(size=20), panel_grid_minor=gg.element_blank())


def _annual_plot_avgmax(activities: pd.DataFrame, subject: str) -> gg.ggplot:
    """Create a faceted plot for the average and max of a value/subject."""
    # Create labels from subject argument
    average_y = f"average_{subject}"
    max_y = f"max_{subject}"
    label_date = datetime.date(2020, 5, 1)  # Hard-coded label position

    # Melt data for plotting
    activities = pd.melt(activities, id_vars=['date_year_agnostic', 'year'], value_vars=[average_y, max_y])

    # Identify the maximum of the maximums and minimum of the averages for labels
    max_2020 = activities[activities["year"] == 2020]["value"].max()
    min_2020 = activities[activities["year"] == 2020]["value"].min()

    # Define function for applying labels
    def label_minmax(x) -> str | None:
        if x["year"] != 2020:
            return None
        if x["value"] == max_2020:
            return f"Maximum {subject}"
        elif x["value"] == min_2020:
            return f"Average {subject}"
        else:
            return None

    # Create labels column
    activities["label"] = activities[["value", "year"]].apply(label_minmax, axis=1)

    plot_colour = pt.heartrate if subject == "heartrate" else pt.velocity
    # Return plot
    return ggplot(activities, aes(x="date_year_agnostic")) \
        + gg.scale_x_datetime(date_breaks="1 month", date_labels="%b") \
        + gg.scale_color_manual(values=[plot_colour, pt.text], guide=False) \
        + gg.geom_point(aes(y="value", color="variable"), size=3) \
        + gg.geom_label(aes(y="value", label="label", color="variable"), fill=pt.background, x=label_date, size=18, ha="left", va='baseline') \
        + gg.facet_grid('. ~ year') \
        + gg.geom_smooth(aes(y="value", color="variable"), span=0.7, size=2.5, se=False) \
        + pt.gg_theme() + annual_theme


def _annual_plot_single(activities: pd.DataFrame, subject: str) -> gg.ggplot:
    """Create a faceted plot for a single value/subject."""
    # Return plot
    return ggplot(activities, aes(x="date_year_agnostic")) \
        + gg.scale_x_datetime(date_breaks="1 month", date_labels="%b") \
        + gg.geom_point(aes(y=subject), size=3, color=pt.heartrate) \
        + gg.facet_grid('. ~ year') \
        + pt.gg_theme() + annual_theme
    

def annual_time(activities: pd.DataFrame):
    """Create a plot showing the average speed vs. time of day."""
    activities["time"] = activities["start_date_local"].map(lambda x: x.replace(year=1970, month=1, day=1))

    return ggplot(activities, aes(x="time", y="average_speed", color="factor(year)", size="distance")) \
        + gg.geom_point(alpha=0.6) \
        + gg.scale_x_datetime(date_breaks="2 hour", date_labels="%H:%M") \
        + gg.scale_color_manual(values=[pt.altitude, pt.velocity, pt.heartrate], guide=False) \
        + gg.scale_size_continuous(range=(1, 7), guide=False) \
        + gg.labs(x="Time of Day", y="Average Speed [km/h]") \
        + pt.gg_theme() + annual_theme


def annual_plot(activities: pd.DataFrame, subject: str) -> gg.ggplot:
    """Create a faceted plot for value/subject"""
    if subject == "heartrate":
        return _annual_plot_avgmax(activities, "heartrate") \
            + gg.labs(x="", y="Heartrate [bpm]")
    elif subject == "speed":
        return _annual_plot_avgmax(activities, "speed") \
            + gg.labs(x="", y="Speed [km/h]")
    elif subject == "distance":
        return _annual_plot_single(activities, "distance/1000") \
            + gg.labs(x="", y="Distance [km]")
    elif subject == "elevation":
        return _annual_plot_single(activities, "total_elevation_gain") \
            + gg.labs(x="", y="Elevation [m]")
    else:  # Plot the annual time chart by default
        return annual_time(activities)
