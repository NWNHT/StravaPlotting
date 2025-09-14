#!/usr/bin/env conda run -n env_general python
# The above is the shebang to be able to run this in the specific conda environment
# This can be run as "./generate_plots.py ...", including any aguments

from strava.data.strava_requests import *
from strava.data.segment_access import *
from strava.plotting.strava_annual_plots import *
from strava.plotting.strava_stream_plots import *
from strava.plotting.segment_plots import *

import argparse
import datetime
import os

import pandas as pd
from warnings import filterwarnings

# Filter out Plotnine "Saving file" warnings
filterwarnings('ignore', message="Saving.*")
# Filter out Plotnine "Filename" warnings
filterwarnings('ignore', message="Filename.*")


def main():
    # Select the dark theme for plots
    pt.dark()

    # Parse arguments, returns argument namespace
    args = parse_arguments()

    # Request list of all activities
    activities = get_clean_activities()

    plot_filepath = '../plots/'

    # Create the annual plots unless indicated otherwise
    if not args.stream_plots_only:
        pt.background = None
        print("Creating annual plots...")
        # Create and save plots
        create_annual_plots(activities=activities, plot_filepath=plot_filepath)
        print("...completed annual plots.")

    # Create the stream plots unless indicated otherwise
    if not args.annual_plots_only:
        # Check that the activity exists, if it does not, then just get the latest activity
        if args.date not in activities["start_date_local"].apply(lambda x: x.date()).values:
            args.date = activities.iloc[0]["start_date_local"].date()
            print(f"No activity available, instead continuing with date {args.date.isoformat()}.")
        print(f"Creating stream plots for activity {activity_id_by_date(activities=activities, date=args.date)} on date {args.date.isoformat()}...")
        # Create cache object
        cache = Cache()
        activity_cache = Cache(dir='/Users/lucasnieuwenhout/Documents/Programming/Python/Projects/StravaPlotting/activity_cache/')

        # Get the stream for specified activity
        stream = get_clean_stream(activities=activities, date=args.date, cache=cache)

        # Create and save plots
        create_stream_plots(stream=stream, date=args.date, plot_filepath=plot_filepath)
        print("...completed stream plots.")

        # Segment
        create_segments(activities=activities, activity_cache=activity_cache, date=args.date)


def create_annual_plots(activities: pd.DataFrame, plot_filepath: str):
    """Create and save annual plots from data in activities dataframe"""
    # Create the annual plots
    subjects = ["heartrate", "speed", "distance", "elevation", "annual_time"]
    plots = [annual_plot(activities=activities, subject=x) for x in subjects]

    # Save the plots
    transparent_background = True
    for i in range(len(subjects)):
        filename = plot_filepath + f"annual/{subjects[i]}.png"
        plots[i].save(filename=filename, format="png", height=9, width=22, transparent=transparent_background)


def create_stream_plots(stream: pd.DataFrame, date: datetime.date, plot_filepath: str):
    """Create and save stream plots from data in the stream dataframe"""
    # Create plots
    heartrate_plot = heartrate_with_altitude(stream=stream)
    velocity_plot = velocity_with_altitude(stream=stream)
    (heartrate_zone_plot, zone_plot) = heartrate_zones(stream=stream, heartrate_max=191)
    summary = all_streams(stream, alpha=0.1)

    # Save the plots
    plot_height = 24
    plot_width = 48
    transparent_background = True

    # Component plot filepath
    component_plot_filepath = plot_filepath + '/plot_components/'

    heartrate_plot.save(filename=component_plot_filepath + "heartrate_plot.png",
                        format="png",
                        height=plot_height, width=plot_width,
                        limitsize=False,
                        transparent=transparent_background)
    velocity_plot.save(filename=component_plot_filepath + "velocity_plot.png",
                       format="png",
                       height=plot_height, width=plot_width,
                       limitsize=False,
                       transparent=transparent_background)
    heartrate_zone_plot.save(filename=component_plot_filepath + "heartrate_zone_plot.png",
                             format="png",
                             height=plot_height, width=plot_width,
                             limitsize=False,
                             transparent=transparent_background)
    zone_plot.save(filename=component_plot_filepath + "zone_plot.png",
                   format="png",
                   height=4, width=48,
                   limitsize=False,
                   transparent=transparent_background)
    summary.save(filename=component_plot_filepath + "stream_summary.png",
                 format="png",
                 height=plot_height, width=plot_width,
                 limitsize=False,
                 transparent=transparent_background)

    # Create a single image from the plots
    id = stream.iloc[0]["id"]
    with open(plot_filepath + f"summary_{date.isoformat()}_{id}.png", "wb") as fp:
        combine_plots_vertical(["velocity_plot.png", 
                                "heartrate_plot.png", 
                                "heartrate_zone_plot.png",
                                "zone_plot.png"],
                               plot_filepath='../plots/plot_components/'
                                ).save(fp=fp, format="png")


def create_segments(activities: pd.DataFrame, activity_cache: Cache, date: datetime.date):

    # Set up paths
    segments_path = r'/Users/lucasnieuwenhout/Documents/Programming/Python/Projects/StravaPlotting/plots/segments/'
    latest_segments_path = r'/Users/lucasnieuwenhout/Documents/Programming/Python/Projects/StravaPlotting/plots/latest_segments/'
    segment_save_paths = [segments_path, latest_segments_path]

    # Create catalog of segments
    segment_catalog = create_segment_catalog(activities, activity_cache)

    # Retrieve segments and plot
    ride_segments = segment_id_from_activity_date_and_index(activities=activities,
                                                            activity_cache=activity_cache,
                                                            activity_date=date,
                                                            entire_list=True)
    os.system(f'rm {latest_segments_path}*')
    for segment_id in ride_segments:
        segment_effort_graph(segment_catalog=segment_catalog,
                            segment_id=segment_id,
                            segment_plot_path=segment_save_paths,
                            previous_x=8)


def get_clean_stream(activities: pd.DataFrame, date: datetime.date, cache: Cache):
    """Retrieve stream of specific activity and clean(column rename and unit conversion)"""
    # Retrieve stream by date
    stream = create_stream_df(get_activity_stream_by_date(activities=activities,
                                                          date=date,
                                                          cache=cache),
                              activity_id_by_date(activities=activities,
                                                  date=date))

    # Rename a column
    stream = stream.rename({"velocity_smooth": "velocity"}, axis=1)
    # Convert speed units
    stream["velocity"] = stream["velocity"] * 3.6

    return stream


def get_clean_activities():
    """Retrieve dataframe of all activities and clean(remove columns, convert to date, convert units, filter out some activities, add some date columns)"""
    # Retrieve data and create df
    activities_list = retrieve_activities()
    activities_df = pd.json_normalize(activities_list)

    # Select only interesting columns
    columns_of_interest = ["id", "name", "distance", "moving_time", "elapsed_time", "total_elevation_gain",
                           "elev_high", "elev_low", "sport_type", "start_date_local", "timezone", "start_latlng",
                           "end_latlng", "achievement_count", "map.id", "workout_type", "average_speed", "max_speed",
                           "average_heartrate", "max_heartrate", "map.summary_polyline"]
    activities_df = activities_df[columns_of_interest]

    # Convert dates and times to datetime
    activities_df["start_date_local"] = pd.to_datetime(activities_df["start_date_local"], format="%Y-%m-%dT%H:%M:%SZ")
    for s in ["moving_time", "elapsed_time"]:
        activities_df[s] = pd.to_timedelta(activities_df[s], unit='S')

    # Create a column holding only the year and a column holding a date with fixed year
    activities_df["year"] = activities_df["start_date_local"].apply(lambda x: x.year)
    activities_df["date_year_agnostic"] = activities_df["start_date_local"].apply(lambda x: x.replace(year=1970))

    # Adjust units for speed
    activities_df[["average_speed", "max_speed"]] = activities_df[["average_speed", "max_speed"]] * 3.6

    # Filter out some activities
    activities_df = activities_df.loc[activities_df.sport_type == "Ride"]  # Select only bicycling activities
    activities_df = activities_df.loc[activities_df.max_speed > 0.1]  # Remove any throwaway activities
    activities_df = activities_df.loc[activities_df.average_heartrate > 145]  # Remove any activities where I wasn't trying that hard

    return activities_df


def parse_arguments():
    """Parse command line arguments, return namespace object"""
    parser = argparse.ArgumentParser(prog="Strava Activity Plot Generator",
                                     description="A script to generate plots from Strava Activities.")

    # Add argument for specifying the date, defaults to the current date
    # - When actually running the script, if the date given is not available then it will just get the latest effort
    parser.add_argument("-d", "--date",
                        dest="date",
                        action="store",
                        default=datetime.date.today(),
                        type=lambda x: datetime.date.fromisoformat(x))

    # Arguments to optionally only make stream or annual plots, default to False
    parser.add_argument("-s", "--stream_only",
                        dest="stream_plots_only",
                        action="store_true")
    parser.add_argument("-a", "--annual_only",
                        dest="annual_plots_only",
                        action="store_true")

    # This is here specifically for testing so that I can specify a date where there is actually
    #   an activity.  In production the default will be the current day, falling back to the most
    #   recent activity if not present.
    # parser.set_defaults(date=datetime.date(2022, 9, 27))

    return parser.parse_args()


if __name__ == "__main__":
    main()
