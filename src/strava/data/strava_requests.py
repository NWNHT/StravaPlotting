# This contains functions for requesting activities and activity streams from Strava.
# This is constructed as a cleaner version of the functions in stravaTesting.ipynb and works together with the Cache class from cache.py

from .cache import Cache

from datetime import date
import json
import requests
import pandas as pd
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

auth_url = "https://www.strava.com/oauth/token"
activities_url = "https://www.strava.com/api/v3/athlete/activities"
activity_detail_url = "https://www.strava.com/api/v3/activities"
stream_url = "https://www.strava.com/api/v3/activities/"

tokens_filepath = "../.config/strava_tokens.txt"

def is_access_valid(expiry: int) -> bool:
    """Check if the Strava access token is still valid."""
    return time.time() + 100 < expiry

def get_access_token() -> str:
    """Read json file storing most recent information, if valid then return, else request new token with refresh token."""
    try:
        with open(tokens_filepath) as fh:
            tokens = json.load(fh)
    except:
        quit("Failed to read token file.")
    
    if is_access_valid(tokens["expires_at"]):
        # return the valid access token
        print("Existing access token is valid.")
        return tokens["access_token"]
    else:
        # Request new access and refresh tokens
        print("Requesting new token...")
        # These values are hard-coded as retrieved from Strava
        payload = {
            'client_id': "93786",
            'client_secret': "6054bcb3a50e5fa8769868f4d8273123db037ede",
            'refresh_token': tokens["refresh_token"],
            'grant_type': "refresh_token",
            'f': 'json'
        }

        res = requests.post(auth_url, data=payload, verify=False)
        try:
            with open(tokens_filepath, "w") as fh:
                json.dump(res.json(), fh)
            print("Token received.")
        except:
            quit("Failed to write response to file.")

        return res.json()["access_token"]

def request_streams(activ_id: int, streams="distance,time,altitude,velocity_smooth,heartrate,moving,latlng"):
    """Request streams from Strava api"""
    # Set up request parameters
    header = {'Authorization': 'Bearer ' + get_access_token()}
    params = {"keys": streams, "key_by_type": True}
    url = stream_url + str(activ_id) + "/streams"

    # Request the streams
    stream_resp = requests.get(url, params=params, headers=header)
    if stream_resp.status_code != 200:
        print(f"Request failed, status code: {stream_resp.status_code}")
        return None
    
    print(f"Received {len(stream_resp.content)} bytes.")
    return stream_resp.content

def get_activity_stream(activities, activ_id: int, cache: Cache, streams="distance,time,altitude,velocity_smooth,heartrate,moving,latlng", ignore_cache=False) -> str | None:
    """Get the specified activity streams for the activity specified by id."""
    # Check that the activity id is in the list of activities, else return empty df
    if activ_id not in activities.id.array:
        print("Activity not found, not requesting stream.")
        return None
    
    # Check cache, if not present then request
    if ignore_cache or cache.cache_contains(activ_id=activ_id) is None:
        response = request_streams(activ_id=activ_id, streams=streams)
        if response is None:
            print("Unable to find in cache and unable to retrieve from Strava.  Returning None.")
            return None
        else:
            cache.cache_json(activ_id=activ_id, text=response)
    else:
        # print(f"Found activity {activ_id} in cache.")
        pass

    # Read the file from the cache
    stream_resp = cache.retrieve_stream(activ_id=activ_id)

    return stream_resp

def get_activity_stream_by_date(activities, date: date, cache: Cache, streams="distance,time,altitude,velocity_smooth,heartrate,moving,latlng", index=0) -> str | None:
    """Get specified activity streams for activity specified by date. If multiple on same day then this will choose the first by default."""
    id_of_activity = activities.id.loc[activities.start_date_local.apply(lambda x: x.date()) == date].values[index]
    return get_activity_stream(activities=activities, activ_id=id_of_activity, streams=streams, cache=cache)

def activity_id_by_date(activities: pd.DataFrame, date: date, index=0) -> int:
    """Utility to return the id of an activity given a datetime.date object."""
    return activities.id.loc[activities.start_date_local.apply(lambda x: x.date()) == date].values[index]

def retrieve_activities() -> list:
    """Retrieve all activities from strava."""
    # Loop variables
    num_per_page = 200
    page = 1
    data = list()

    # Header for request
    header = {'Authorization': 'Bearer ' + get_access_token()}

    print("Beginning request of activities...")
    while True:
        param = {'per_page': num_per_page, 'page': page}
        page_of_data = requests.get(activities_url, headers=header, params=param).json()
        data = data + page_of_data
        print(f"-> Received page {page} with {len(page_of_data)} activities.")

        if not len(page_of_data):
            print(f"...retrieved total of {len(data)} activities.")
            return data
        else:
            page += 1

def list_activities(activities: pd.DataFrame) -> None:
    """Given dataframe of activities, list all activities in some easily readable way."""
    # Function to apply to each row of the dataframe given
    def create_summary_string(activities) -> str:
        seconds = activities.moving_time.total_seconds()
        summary_string = f"{activities.start_date_local.date()} - Rode {activities.distance/1000:4.2f}km in {seconds // 3600:02.0f}:{seconds % 3600 // 60:02.0f}:{seconds % 60:02.0f}. ID: {activities.id}."
        return summary_string
    
    print("Summary of Activities:")
    activities.apply(create_summary_string, axis=1).apply(print)

def create_stream_df(data_str: str, activ_id: int) -> pd.DataFrame:
    """Create a dataframe from the Strava stream JSON, this includes adding a variable for the activity id."""
    stream_df = pd.DataFrame()
    if data_str is None:
        return None
    else:
        for k, v in json.loads(data_str).items():
            stream_df[k] = v["data"]
    stream_df["id"] = activ_id
    return stream_df

def request_activity(activity_id: int, include_all_efforts: bool=True):
    """Request activity data."""

    # Set up request parameters
    header = {'Authorization': 'Bearer ' + get_access_token()}
    params = {"include_all_efforts": include_all_efforts}
    url = activity_detail_url + '/' + str(activity_id)

    # Request the streams
    stream_resp = requests.get(url, params=params, headers=header)
    if stream_resp.status_code != 200:
        print(f"Request failed, status code: {stream_resp.status_code}")
        return None

    print(f"Received {len(stream_resp.content)} bytes.")
    return stream_resp.content

def get_activity_detail(activities, activ_id: int, cache: Cache, include_all_efforts: bool=True, ignore_cache=False) -> str | None:
    """Get the specified activity streams for the activity specified by id."""
    # Check that the activity id is in the list of activities, else return empty df
    if activ_id not in activities.id.array:
        print("Activity not found, not requesting stream.")
        return None
    
    # Check cache, if not present then request
    if ignore_cache or cache.cache_contains(activ_id=activ_id) is None:
        response = request_activity(activity_id=activ_id, include_all_efforts=include_all_efforts)
        if response is None:
            print("Unable to find in cache and unable to retrieve from Strava.  Returning None.")
            return None
        else:
            cache.cache_json(activ_id=activ_id, text=response)
    else:
        # print(f"Found activity {activ_id} in cache.")
        pass

    # Read the file from the cache
    stream_resp = cache.retrieve_stream(activ_id=activ_id)

    # Convert from JSON, some required cleaning for backslashes
    stream_resp = json.loads(stream_resp.encode('utf-8').decode('unicode_escape'))

    return stream_resp

