
import pandas as pd
import plotnine as gg

from strava.plotting.strava_stream_plots import *
pt.light()

def segment_effort_graph(segment_catalog: pd.DataFrame, segment_id: int, segment_plot_path: str=None, previous_x: int=8, save_plot: bool=False):
    """Generaet recent segment effort graph from the segment id.

    Args:
        segment_catalog (pd.DataFrame): Catalog of segments
        segment_id (int): _description_
        previous_x (int, optional): _description_. Defaults to 8.
        save_plot (bool, optional): _description_. Defaults to False.

    Returns:
        _type_: _description_
    """

    # Check inputs
    if previous_x < 3:
        print(f"Must plot at least three points")
        return (None, None)

    # Generate the segment link
    segment_link = f'https://www.strava.com/segments/{segment_id}'
    
    # Create the dataframe of segment efforts
    segment = segment_catalog[segment_id]
    plot_df = segment.effort_df
    plot_df_prev = plot_df[plot_df.DateTimeIndex > (plot_df.DateTimeIndex.max() - previous_x)].copy()

    # Filtering and Such?
    # - Potentially filter to only a single effort per activity.  Have to reset the index on the activity, or I could base the index off of time instead of activity ID.

    # Segment Information
    segment_name = plot_df.SegmentName[0]

    # Colours
    ribbon_colour = '#3481E7'
    averages_colour = '#1638E5'
    hr_colour = '#CA1E00'
    pr_colour = '#A343F6'
    # pr_colour = '#1A4F1B'
    # pr_colour = '#5FE4E7'
    # hr_colour = '#E74F59'

    # --- X ---
    # Full Range
    xmin = 0
    # Limit min to previous_x
    xmin = plot_df.DateTimeIndex.max() - previous_x + 0.5 * (previous_x / 8)
    # Full Range
    xmax = plot_df.DateTimeIndex.max() + 0.5 * (previous_x / 8)

    xlim = (xmin, xmax)

    # --- Y ---
    ymin = 0
    # Full Range
    ymin = plot_df['MovingTime[s]'].min() * 0.9
    ymax = plot_df['MovingTime[s]'].max() * 1.1
    # Prevous x
    ymin = plot_df_prev['MovingTime[s]'].min() * 0.9
    ymax = plot_df_prev['MovingTime[s]'].max() * 1.1

    ylim = (ymin, ymax)

    # --- Ribbon ---
    plot_df['xmin'] = xmin
    plot_df['xmax'] = xmax
    plot_df['ymin'] = ymin
    plot_df['ymax'] = ymax

    # --- Labels ---
    plot_df_prev['AverageHRLabel'] = plot_df_prev.AverageHR.apply(lambda x: round(x))

    # --- Averages ---
    alltime_avg = plot_df['MovingTime[s]'].mean()
    window_avg = plot_df_prev['MovingTime[s]'].mean()

    # --- Heartrate Points ---
    plot_df_prev['AverageHRPlot'] = plot_df_prev.AverageHR + plot_df_prev['MovingTime[s]'].mean() - plot_df_prev.AverageHR.mean()

    # --- PR ---
    pr_effort, pr_time = segment.pr()
    pr_label_df = pd.DataFrame({'x': [xmin], 'y': [pr_time - (pr_time / 200)], 'label': [f"fastest: {pr_effort.start_date_local.split('T')[0]}"]})

    # --- Latest Effort Date ---
    latest_effort_date = f"latest: {segment.latest_effort().start_date_local.split('T')[0]}"
    latest_effort_date_label_df = pd.DataFrame({'x': [plot_df.DateTimeIndex.max()], 'y': [ymin], 'label': [latest_effort_date]})

    # --- Plot ---
    g = (gg.ggplot()
        + gg.geom_ribbon(plot_df, gg.aes(x='DateTimeIndex', ymin='ymin', ymax='MovingTime[s]'), fill=ribbon_colour, alpha=0.35)

        + gg.geom_hline(plot_df, gg.aes(yintercept=alltime_avg), size=1, colour=averages_colour, alpha=0.7, linetype='dashed')
        + gg.geom_hline(plot_df, gg.aes(yintercept=window_avg), size=1.5, colour=averages_colour, alpha=0.7)

        + gg.geom_hline(plot_df, gg.aes(yintercept=pr_time), size=1.5, colour=pr_colour, alpha=0.4)
        + gg.geom_text(pr_label_df, gg.aes(x='x', y='y', label='label'), colour=pr_colour, ha='left', va='top', size=12)

        + gg.geom_point(plot_df_prev, gg.aes(x='DateTimeIndex', y='AverageHRPlot'), size=5.5, alpha=0.75, colour=hr_colour)
        + gg.geom_point(plot_df, gg.aes(x='DateTimeIndex', y='MovingTime[s]'), size=6, alpha=0.75, stroke=2.25, colour=ribbon_colour, fill="none")

        + gg.geom_text(plot_df_prev, gg.aes(x=f'DateTimeIndex + {0.010 + previous_x * 0.028}', y='AverageHRPlot', label='AverageHRLabel'), colour=hr_colour, size=12)

        + gg.geom_text(latest_effort_date_label_df, gg.aes(x='x', y='y', label='label'), colour=averages_colour, ha='right', va='bottom', size=12)

        + gg.coord_cartesian(xlim=xlim, ylim=ylim, expand=False)

        + gg.scale_y_continuous(labels=lambda y: [f"{x // 60:0.0f}:{x % 60:02.0f}" for x in y])

        + pt.gg_theme()
        + gg.theme(
                # figure_size=(14, 6),
                figure_size=(10, 4),
                panel_border=gg.element_blank(),
                axis_text=gg.element_text(size=18),
                axis_title=gg.element_text(size=24),
                axis_text_x=gg.element_blank(),
                axis_text_y=gg.element_text(size=14),
                plot_title=gg.element_text(size=20, ha='left'),
                plot_subtitle=gg.element_text(size=10, ha='left'),
                )
        + gg.labs(x="", y="", title=segment_name, subtitle='.'.join(segment_link.split('.')[1:]))
    )

    if save_plot and (segment_plot_path is None):
        print("segment_plot_path not provided, plot not saved.")

    if save_plot:
        g.save(filename=segment_plot_path + f"{segment_id}.png")

    return (g, segment_link)
