#!/usr/bin/python3

import sys
sys.path.append("../libraries/common/")
import threading
import time
import common


Lock = threading.RLock()
Timers = []

class SynchronizedTimer(threading.Timer):
    def __init__(self, delay, func, args, debug=False, info=False):
        self._log = common.initLogger("Timer", debug, info)
        super().__init__(delay, func, args)

    def call(self):
        # TODO: make sure we don't call at the same time. 
        # the function that is called may not be thread safe.
        #with Lock:
        self._log.debug(f"call {self.function.__name__}")
        self.function(*self.args,**self.kwargs)  
        self._log.debug(f"returned from call {self.function.__name__}")

    def __del__(self):
        self._log.debug("interval timer is deleted")



class IntervalTimer(SynchronizedTimer):  
    def run(self):  
        while not self.finished.wait(self.interval):  
            self.call()

def CreateDelayedTimer(delay, func, args, debug=False, info=False):
    t = SynchronizedTimer(delay, func, args, debug, info)
    t.start()

def StartIntervalTimer(t):
    # when we start, call function for the first time
    t.call()
    t.start()

def CreateIntervalTimer(delay, interval, func, args, debug=False, info=False):
    intervalTimer = IntervalTimer(interval, func, args, debug, info)
    Timers.append(intervalTimer)
    if delay > 0.0: 
        # start interval timer with a delay. 
        CreateDelayedTimer(delay, StartIntervalTimer, [ intervalTimer ] )
    else:
        intervalTimer.start()


def CancelAllTimers():
    for timer in Timers:
        timer.cancel()
        timer.join()


# Tests--------------------------------------------------------------
if __name__ == '__main__':
    def display_delayed(data):
        print(f"Display_delayed: {data}")
        j = 0
        for i in range(1,10000):
            j +=i
        print(f"j={j}")

    def display_interval(data):
        print(f"Display_interval: {data}")
        j = 0
        for i in range(1,500000):
            j +=i
        print(f"j={j}")


    CreateDelayedTimer(10, display_delayed, ["delayed 10 seconds ...."], debug=True, info=True)
    CreateDelayedTimer(5, display_delayed, ["delayed 5 seconds ...."], debug=True, info=True)
    CreateIntervalTimer( 3.0, 1.0, display_interval, ["interval 1..."], debug=True, info=True)

    time.sleep(15)
    print("done...")
    print("and canceled all...")
    CancelAllTimers()
