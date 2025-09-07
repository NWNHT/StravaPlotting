
import datetime
import pandas as pd
import requests

from strava.data.cache import Cache
from strava.data.Segment import Segment
from strava.data.strava_requests import get_access_token, get_activity_detail

def request_segment(segment_id: int):
    """Request activity data."""
    segment_effort_url = "https://www.strava.com/api/v3/segments/"

    # Set up request parameters
    header = {'Authorization': 'Bearer ' + get_access_token()}
    url = segment_effort_url + str(segment_id)

    # Request the streams
    stream_resp = requests.get(url, headers=header)
    if stream_resp.status_code != 200:
        print(f"Request failed, status code: {stream_resp.status_code}")
        return None

    print(f"Received {len(stream_resp.content)} bytes.")
    return stream_resp

def create_segment_catalog(activities: pd.DataFrame, activity_cache: Cache, activity_list: pd.DataFrame=None):
    """Create a catalog of the segments and efforts in activity_list.

    Args:
        activities (pd.DataFrame): Standard dataframe of the activities.
        activity_list (pd.DataFrame): Standard activities dataframe, filtered.
        activity_cache (Cache): Cache object of the activity cache.

    Returns:
        dict: Dictionay of {segment_id: Segment}
    """

    if activity_list is None:
        activity_list = activities

    segments = {}
    # For each activity, get the activity detail 
    for act_id in activity_list.id:
        ad = get_activity_detail(activities, act_id, activity_cache, include_all_efforts=True)
        
        # For each effort in the activity
        for effort in ad['segment_efforts']:
            # If the segment is not already in the list, add it
            if effort['segment']['id'] not in segments:
                segments[effort['segment']['id']] = Segment(id=effort['segment']['id'])

            # Add the effort to the segment
            segments[effort['segment']['id']].add_effort(effort)
    
    return segments

def segment_id_from_activity_date_and_index(activities: pd.DataFrame,
                                            activity_cache: pd.DataFrame,
                                            activity_date: datetime.date=datetime.date.today(), 
                                            segment_index: int=0, 
                                            entire_list: bool=False,
                                            print_segments: bool=False):
    """Return the id of a segment from the activity of interest.

    Args:
        activities (pd.DataFrame): Activities dataframe.
        activity_date (datetime.date, optional): The date of the activity. Defaults to datetime.date.today().
        segment_index (int, optional): List index of the segment of interest. Defaults to 0.
        entire_list (bool, optional): Return the entire list of segment ids. Defaults to False.

    Returns:
        int or list: integer of the segment id or a list of all of the segment ids
    """

    # Convert date to activity
    activity_id = activities.id.loc[activities.start_date_local.apply(lambda x: x.date()) == activity_date].values[0] # This is built to just take the first activity from that day
    activity_detail = get_activity_detail(activities, activity_id, activity_cache, include_all_efforts=True)

    segment_id_list = []
    for i, seg in enumerate(activity_detail['segment_efforts']):
        # Add the segment id to the list
        segment_id_list.append(seg['segment']['id'])
        if print_segments: 
            print(f"{i:2}: {seg['segment']['name']}")
        
    if entire_list:
        return segment_id_list
    else:
        return segment_id_list[segment_index]

def effort_link_to_segment_id(activities: pd.DataFrame, activity_cache: Cache, link: str) -> int:
    """Given a link in the style https://www.st{...}es/{activity_id}/segments/{segment_effort_id}, return the segment id.

    Args:
        activities (pd.DataFrame): Activities dataframe.
        activity_cache (Cache): Activity details cache.
        link (str): Link to the segment effort.

    Returns:
        int: Segment id.
    """

    # Chop up link
    activity_id = int(link.split('/')[-3])
    segment_effort_id = int(link.split('/')[-1])
    print(activity_id)

    # Find the segment id from effort list/dict
    segment_effort_dict = {x['id']: x['segment']['id'] for x in get_activity_detail(activities, activ_id=activity_id, cache=activity_cache)['segment_efforts']}
    segment_id = segment_effort_dict[segment_effort_id]

    return segment_id

def segment_link_to_segment_id(link: str) -> int:
    """Given a link in the style http://ww.st{...}ents/{segment_id}?filter=overall, return the segment id.

    Args:
        link (str): Link to the segment detail page.

    Returns:
        int: Segment id.
    """
    # https://www.strava.com/segments/23981846?filter=overall
    return int(link.split('?')[0].split('/')[-1])
