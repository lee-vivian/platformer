from datetime import datetime

from utils import error_exit

"""
Stopwatch object to log time between processes
"""


class Stopwatch:

    def __init__(self):
        self.time = None

    def start(self):
        self.time = datetime.now()

    def stop(self):
        self.time = None

    def get_lap_time_str(self, process_str):
        cur_time = datetime.now()  # get current time
        if self.time is not None:
            lap_time_str = str(cur_time - self.time)  # get lap time str
            self.time = cur_time  # update time
            print("Lap: %s" % str(datetime.now()))
            return "%s runtime: %s" % (process_str, lap_time_str)
        error_exit("Must start stopwatch before getting lap time")

