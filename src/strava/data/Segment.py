
import json
import pandas as pd
import requests

from strava.data.strava_requests import get_access_token
from strava.data.SegmentEffort import SegmentEffort

class Segment:
    # I think that I should make the main method of getting data just to use the effort stats.
    # If I really want to then I can query Stava for the KOM or something

    def __init__(self, id: int):

        self.id = id

        self._segment_content = None

        self._achievements = None

        self._efforts: list[SegmentEffort] = []
        self.number_efforts = 0

        self._effort_df = None

    @property
    def segment_content(self, force: bool=False):

        if not force:
            print(f"If this is done in a loop, it will likely nuke the rate limit.  Currently 200 every 15 minutes, 2000 per day.")
            return None

        if self._segment_content is None:
            self.request_segment_details()
        return self._segment_content
    
    def request_segment_details(self):
        """Request segment data."""
        segment_effort_url = "https://www.strava.com/api/v3/segments/"

        # Set up request parameters
        header = {'Authorization': 'Bearer ' + get_access_token()}
        url = segment_effort_url + str(self.id)

        # Request the streams
        stream_resp = requests.get(url, headers=header)
        if stream_resp.status_code != 200:
            print(f"Request failed, status code: {stream_resp.status_code}")
            return None

        print(f"Received {len(stream_resp.content)} bytes.")

        self._segment_content = json.loads(stream_resp.content)
    
    @property
    def achievements(self):
        if self._achievements is None:
            self._collect_achievements()
        
        return self._achievements
    
    def _collect_achievements(self):
        self._achievements = []
        for e in self.efforts:
            for a in e.achievements:
                self._achievements.append((e, a))
        
        return self._achievements

    def latest_effort(self):
        # Get the latest effort
        latest_effort = self.efforts[0]
        for e in self.efforts:
            if e.start_date_local > latest_effort.start_date_local:
                latest_effort = e
        return latest_effort
    
    def local_legend(self):
        # Returns the date and number if the latest effort has the local legend, None if not
        e = self.latest_effort()
        ea = e.achievements
        for achievement in ea:
            if achievement['type_id'] == 7:
                return (e.start_date_local, achievement['effort_count'])
        return None
    
    def pr(self):
        # Return the fastest time and the effort
        pr_effort = None
        pr_time = 999
        for e in self.efforts:
            if e.elapsed_time <= pr_time:
                pr_time = e.elapsed_time
                pr_effort = e
        
        return (pr_effort, pr_time)
    
    def latest_effort_achievements(self):
        return self.latest_effort()._achievements_raw
    
    @property
    def efforts(self):
        return self._efforts
    
    def _generate_effort_df(self):
        eff_df = []
        for eff in self._efforts:
            eff_rec = [eff.id]
            eff_rec.append(self.id)
            eff_rec.append(eff.activity_id)
            eff_rec.append(eff.segment_name)
            eff_rec.append(eff.elapsed_time)
            eff_rec.append(eff.moving_time)
            eff_rec.append(eff.start_date_local)
            eff_rec.append(eff.average_heartrate)
            eff_rec.append(eff.max_heartrate)
            eff_rec.append(eff.pr_rank)
            eff_df.append(eff_rec)
        
        # Combine to df
        eff_df = pd.DataFrame(eff_df, columns=['EffortID', 'SegmentID', 'ActivityID', 'SegmentName', 'ElapsedTime[s]', 'MovingTime[s]', 'StartDateLocal', 'AverageHR', 'MaxHR', 'PRRank'])

        # Clean and util
        eff_df['DateTime'] = pd.to_datetime(eff_df.StartDateLocal)
        eff_df = eff_df.sort_values('DateTime').reset_index(drop=True)
        eff_df['DateTimeIndex'] = range(1, len(eff_df) + 1)

        activity_index_lookup = {x: i for i, x in enumerate(sorted(eff_df.ActivityID.unique()))}
        eff_df['ActivityIndex'] = eff_df.ActivityID.map(activity_index_lookup)

        return eff_df
    
    @property
    def effort_df(self):
        if self._effort_df is None:
            self._effort_df = self._generate_effort_df()
        
        return self._effort_df
    
    def add_effort(self, effort):
        self._efforts.append(SegmentEffort(effort))
        self.number_efforts += 1
    
    def seg_data(self):
        if not self.number_efforts:
            return None
        
        return self._efforts[0].segment
    
    def __str__(self):
        return f"Segment: {self.id}, {self.number_efforts} efforts"
    
    def __eq__(self, other):
        return isinstance(other, Segment) and self.id == other.id
