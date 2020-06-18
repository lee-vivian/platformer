from datetime import datetime

from utils import error_exit

"""
Stopwatch object to log time between processes
"""


class Stopwatch:

    def __init__(self):
        self.time = None
        self.start_time = None
        self.stop_time = None

    def start(self):
        self.start_time = datetime.now()
        self.time = self.start_time

    def stop(self):
        self.stop_time = datetime.now()
        self.time = None
        runtime = str(self.stop_time - self.start_time)
        print("Total runtime: %s" % runtime)
        return runtime

    def get_lap_time_str(self, process_str):
        cur_time = datetime.now()  # get current time
        if self.time is not None:
            lap_time_str = str(cur_time - self.time)  # get lap time str
            self.time = cur_time  # update time
            print("Lap: %s" % str(datetime.now()))
            return "%s runtime: %s" % (process_str, lap_time_str)
        error_exit("Must start stopwatch before getting lap time")

