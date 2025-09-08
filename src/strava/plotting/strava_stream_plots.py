# Contains functions for creating ggplots from a Strava activity stream

import copy
import pandas as pd
from plotnine import ggplot, aes
import plotnine as gg
from typing import List
from PIL import Image

# Colours
stred = '#f83a07'
light = "#ecffff"
dark = "#103a5a"
gray = "#AAAAAA"
darkdarkgray = "#1c1d1c"
heartrate_colour = stred
velocity_colour = "blue"
altitude_colour = "lightgray"


# Theme class, will default to light theme unless specified by user.
class PlotTheme:
    def __init__(self, mode=False):
        # True for dark mode, False for light
        self.mode = mode
        self.text = self.background = self.velocity = self.heartrate = self.altitude = self.yint = self.strip = None
        if mode:
            self.light()
        else:
            self.dark()

    def dark(self):
        self.text = light
        self.background = dark
        self.velocity = "cyan"
        self.heartrate = stred
        self.altitude = "lightgray"
        self.yint = "gray"
        self.strip = "gray"

    def light(self):
        self.text = gray
        self.background = light
        self.velocity = "blue"
        self.heartrate = stred
        self.altitude = "gray"
        self.yint = "gray"
        self.strip = "gray"

    def gg_theme(self):
        return gg.theme_light() + gg.theme(text=gg.element_text(color=self.text, size=40),
                                           axis_title_x=gg.element_text(size=60),
                                           axis_title_y=gg.element_text(size=60),
                                           figure_size=(30, 20),
                                           strip_background=gg.element_rect(fill=self.strip),
                                           plot_background=gg.element_rect(fill=self.background),
                                           panel_background=gg.element_rect(fill=self.background),
                                           panel_grid=gg.element_line(color=self.text),
                                           panel_grid_minor=gg.element_line(color=self.text))


pt = PlotTheme()
pt.dark()

def ybreaks(limits):
    """Utility to define the breaks for heartrate plots."""
    return [x for x in range(int(limits[0]), int(limits[1])) if (x % 10 == 0)]


def heartrate_zones(stream: pd.DataFrame, heartrate_max: int, zones: List[float] = None):
    """Plot heartrate with background color indicating heartrate zone.
    - Returns two plots"""
    if zones is None:
        zones = [0.6, 0.7, 0.8, 0.9]

    def make_heartrate_zone_function(zones):
        """Return a closure for computing the heartrate zones."""

        def heartrate_zone_classifier(x):
            for i, z in enumerate(zones):
                if x < z:
                    return i + 1
            return 5

        return heartrate_zone_classifier

    zones = [x * heartrate_max for x in zones]
    classifier = make_heartrate_zone_function(zones)

    stream = copy.deepcopy(stream)
    stream["heartrate_altitude"] = ((stream.altitude - stream.altitude.min()) * (stream.heartrate.max() / (
            stream.altitude.max() - stream.altitude.min()))) + 0.05 * stream.heartrate.max()
    stream["zones"] = stream.heartrate.apply(classifier)
    stream["zones"] = pd.Categorical(stream["zones"], categories=[5, 4, 3, 2, 1], ordered=True)
    stream["distance_offset"] = stream.distance.shift(-1)
    stream["heartrate"] = stream["heartrate"].rolling(10).mean()

    max_value = stream["heartrate"].max()
    min_value = stream["heartrate"].min()

    zone_colors = ["#ee0d0d", "#ff4f00", "#17c903", "#16e276", "#1e8ef0"]

    return (ggplot(stream, aes(x="distance/1000", ymax="heartrate_altitude"))
            + gg.scale_y_continuous(limits=[min_value * 0.9, max_value * 1.01], breaks=ybreaks, expand=[0, 0])
            + gg.scale_x_continuous(limits=[0, stream.distance.max() / 1000], expand=[0, 0])
            + gg.geom_rect(
        aes(xmin="distance/1000", xmax="distance_offset/1000", ymin=min_value * 0.9, ymax=max_value * 1.01,
            fill="factor(zones)"), alpha=0.5)
            + gg.scale_fill_manual(values=zone_colors, guide=None)
            + gg.geom_line(aes(y="heartrate"), color=pt.text, size=2.5)
            + gg.geom_hline(yintercept=zones, color=pt.yint, size=1.5)
            + gg.xlab("Distance [km]") + gg.ylab("Heartrate [bpm]") + gg.labs(fill="Zone")
            + pt.gg_theme(),
            ggplot(stream)
            + gg.geom_bar(aes(x=1, fill="factor(zones)"), alpha=1)
            + gg.scale_x_continuous(expand=[0, 0])
            + gg.scale_fill_manual(values=zone_colors, guide=None)
            + gg.coord_flip()
            + gg.xlab("") + gg.ylab("")
            + pt.gg_theme() + gg.theme(axis_text_y=gg.element_blank(), axis_text_x=gg.element_blank(),
                                       panel_grid=gg.element_blank()))


def heartrate_with_altitude(stream: pd.DataFrame, rolling_average=10):
    """Plot heartrate vs. distance with altitude in the background."""
    stream = copy.deepcopy(stream)
    stream["heartrate"] = stream["heartrate"].rolling(rolling_average).mean()
    stream["altitude"] = stream["altitude"].rolling(10).mean()
    max_value = stream["heartrate"].max()
    min_value = stream["heartrate"].min()
    min_value_buffer = min_value - (max_value - min_value) * 0.1
    max_altitude = stream["altitude"].max()
    min_altitude = stream["altitude"].min()
    stream["heartrate_altitude"] = ((stream.altitude - min_altitude) * (max_value - min_value) / (
            max_altitude - min_altitude)) + min_value

    return ggplot(stream, aes(x="distance/1000")) \
           + gg.scale_y_continuous(limits=[min_value_buffer, max_value * 1.01], breaks=ybreaks, expand=[0, 0]) \
           + gg.scale_x_continuous(limits=[0, stream.distance.max() / 1000], expand=[0, 0]) \
           + gg.geom_ribbon(aes(ymin=min_value_buffer, ymax="heartrate_altitude"), fill=pt.altitude, color=pt.altitude,
                            size=1, alpha=0.3) \
           + gg.geom_ribbon(aes(ymin=min_value_buffer, ymax="heartrate"), fill=pt.altitude, color=pt.heartrate,
                            size=2.5, alpha=0.2) \
           + gg.xlab("Distance [km]") + gg.ylab("Heartrate [bpm]") \
           + pt.gg_theme()


def velocity_with_altitude(stream: pd.DataFrame, rolling_average=30):
    """Plot velocity vs. distance with altitude in the background."""
    stream = copy.deepcopy(stream)

    stream.rename({"velocity_smooth": "velocity"}, axis=1, inplace=True)
    stream["velocity"] = stream["velocity"] * 3.6
    stream["velocity"] = stream["velocity"].rolling(rolling_average).mean()
    stream["altitude"] = stream["altitude"].rolling(10).mean()
    max_value = stream["velocity"].max()
    min_value = stream["velocity"].min()
    min_value_buffer = min_value - (max_value - min_value) * 0.1
    max_altitude = stream["altitude"].max()
    min_altitude = stream["altitude"].min()
    stream["velocity_altitude"] = ((stream.altitude - min_altitude) * (max_value - min_value) / (
            max_altitude - min_altitude)) + min_value

    def to_strings(array):
        return [f"{x:3.1f}" for x in array]

    return ggplot(stream, aes(x="distance/1000")) \
           + gg.scale_y_continuous(limits=[min_value_buffer, max_value * 1.01], expand=[0, 0], labels=to_strings) \
           + gg.scale_x_continuous(limits=[0, stream.distance.max() / 1000], expand=[0, 0]) \
           + gg.geom_ribbon(aes(ymin=min_value_buffer, ymax="velocity_altitude"), fill=pt.altitude, color=pt.altitude,
                            size=1, alpha=0.3) \
           + gg.geom_ribbon(aes(ymin=min_value_buffer, ymax="velocity"), fill=pt.altitude, color=pt.velocity, size=2.5,
                            alpha=0.2) \
           + gg.xlab("Distance [km]") + gg.ylab("Velocity [km/h]") \
           + pt.gg_theme()


def all_streams(stream: pd.DataFrame, rolling_average_hr=10, rolling_average_vel=30, alpha=0.1):
    """Plot heartrate vs. distance with altitude in the background."""
    stream = copy.deepcopy(stream)
    stream["heartrate"] = stream["heartrate"].rolling(rolling_average_hr).mean()
    stream.rename({"velocity_smooth": "velocity"}, axis=1, inplace=True)
    stream["velocity"] = stream["velocity"] * 3.6
    stream["velocity"] = stream["velocity"].rolling(rolling_average_vel).mean()
    stream["altitude"] = stream["altitude"].rolling(10).mean()

    # Scale the streams to 0-1 range
    for cat in ["heartrate", "velocity", "altitude"]:
        stream[cat] = (stream[cat] - stream[cat].min()) / (stream[cat].max() - stream[cat].min())

    return ggplot(stream, aes(x="distance/1000")) \
           + gg.scale_y_continuous(limits=[0, 1], expand=[0, 0]) \
           + gg.scale_x_continuous(limits=[0, stream.distance.max() / 1000], expand=[0, 0]) \
           + gg.geom_ribbon(aes(ymin=0, ymax="altitude"), fill=pt.altitude, color=pt.altitude, size=1, alpha=0.3) \
           + gg.geom_ribbon(aes(ymin=0, ymax="heartrate"), fill=pt.heartrate, color=pt.heartrate, size=2.5, alpha=alpha) \
           + gg.geom_ribbon(aes(ymin=0, ymax="velocity"), fill=pt.velocity, color=pt.velocity, size=2.5, alpha=alpha) \
           + gg.xlab("Distance [km]") + gg.ylab("") \
           + pt.gg_theme() + gg.theme(axis_text_y=gg.element_blank())


def combine_plots_vertical(images: List, plot_filepath: str='../plots/') -> Image.Image:
    """Combine all of the stream plots into a single image."""
    images = [Image.open(plot_filepath + x) for x in images]
    widths, heights = zip(*(i.size for i in images))

    total_width = max(widths)
    total_height = sum(heights)

    # Resize images to the same width, the max width of the images
    images = [im.resize((total_width, im.size[1])) for im in images]

    new_im = Image.new('RGB', (total_width, total_height))
    x_offset = 0
    for im in images:
        new_im.paste(im, (0, x_offset))
        x_offset += im.size[1]

    return new_im
