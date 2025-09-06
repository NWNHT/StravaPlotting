
class SegmentEffort:
    
    def __init__(self, effort):

        self.id = effort['id']
        self.activity_id = effort['activity']['id']
        self.segment_name = effort['name']
        self.elapsed_time = effort['elapsed_time']
        self.moving_time = effort['moving_time']
        self.start_date_local = effort['start_date_local']
        self.average_heartrate = effort['average_heartrate']
        self.max_heartrate = effort['max_heartrate']
        self.pr_rank = effort['pr_rank']
        self._achievements_raw = effort['achievements']
        self._achievements = None
        self._ll = None
        self._ll_count = None
        self.segment = effort['segment']
    
    @property
    def achievements(self):
        self._achievements = self._achievements_raw
        return self._achievements
    
    def _this_isnt_useful_right_now(self):
        # This has the flaw that it will return the overall achievement even if it has been overtaken
        # This is not a reliable way to tell if I have the pr
        # - It should be a reliable way to grad the ll though, that updates whenever you have it I think
        print(self.id)
        self._ll = False
        self._ll_count = 0
        for a in self._achievements_raw:
            if a['type_id'] == 7:
                self._ll = True
                if a['effort_count'] > self._ll_count:
                    self._ll_count = a['effort_count']
            
        return self._achievements_raw
