from sys import argv
from os import system
from time import sleep
import threading, datetime, random

class Beeper(threading.Thread):
  """Beeper object that beeps on another thread until stopped.
  
  Subclasses Thread and overrides the run method to beep.

  Member Variables:
    _beep boolean indicating if the Beeper should beep.
      Call stop() to set this to False and terminate the thread.

  """

  def __init__(self):
    """Initialize a Beeper."""

    threading.Thread.__init__(self, None, None, None, (), {})
    self._beep = True
    
  def run(self):
    """Beep and wait a certain interval until stop() is called."""

    while self._beep:
      Alarm.BEEP()
      Alarm.SLEEP(Alarm.BEEP_INTERVAL)

  def stop(self): 
    """Stop the beeping thread."""

    self._beep = False

class Alarm(object):
  """Alarm object.
  
  Class Variables:
    SLEEP_MSG
    ACCLIMATE_LENGTH
    BEEP_INTERVAL
    CODE_LENGTH
    LOG_PATH
    DICT_PATH

  Member Variables:
    wakeupTime
    acclimate
    _beep
    _dict
    
  """

  SLEEP_MSG = ("Sweet Dreams","Goodnight")
  ACCLIMATE_LENGTH = 5 * 60
  BEEP_INTERVAL = .5
  CODE_LENGTH = (4,8)
  LOG_PATH = "./.sleeplog"
  DICT_PATH = "/etc/dictionaries-common/words"

  def __init__(self, wakeupTime, acclimate=False):
    """Initialize an Alarm given wakeup time and optional acclimate boolean"""

    self.wakeupTime = wakeupTime
    self.acclimate = acclimate
    self._beeper = Beeper()
    self._dict = {}

  @staticmethod
  def BEEP():
    """Make the computer beep by internal speaker."""

    system("beep -e /dev/input/by-path/platform-pcspkr-event-spkr")

  @staticmethod
  def SLEEP(seconds):
    """Sleep for a given number of seconds without using cpu."""

    sleep(seconds)

  @staticmethod
  def ACCLIMATE_PATTERN(iteration):
    """Return an exponential regression for a given iteration."""

    return .5274 * iteration**(-1.5214))

  def startBeeps(self):
    """Start a beep thread and beep until stop is called."""

    self._beeper.start()

  def loadDict(self):
    """Load all entries fom DICT_PATH into _dict."""

    with file(Alarm.DICT_PATH, "r") as f:
      i = 0
      for line in f.readlines():
        self._dict[i] = line
        i+=1

  def startAlarm(self):
    """Start the alarm clock and sleep."""

    now = datetime.datetime.today()
    wait = (self.wakeupTime - now).total_seconds()
    self.logSleep(now, wait)
    self.loadDict() #load the dictionary
    if self.acclimate and wait > Alarm.ACCLIMATE_LENGTH: 
      Alarm.SLEEP(wait - Alarm.ACCLIMATE_LENGTH)
      for i in range(1,6):
        Alarm.BEEP()
        Alarm.SLEEP(Alarm.ACCLIMATE_LENGTH * Alarm.ACCLIMATE_PATTERN(i))
    else:
      self.SLEEP(wait)
    #Start beeping
    self.startBeeps()

  def stopAlarm(self):
    """Stop the alarm clock when the user enters the correct word sequence."""

    start = datetime.datetime.today()
    stopCode = " ".join(lambda: self._dict[random.randint(len(self._dict))] \
      for _ in range(random.randint(*Alarm.CODE_LENGTH)))

    while raw_input(stopCode) != stopCode: pass
    stop = datetime.datetime.today()
    #mark dictionary for garbage collection
    self._dict = None 
    self._beeper.stop()
    logStop(stop - start)

  def logSleep(date, sleepTime):
    """Write to the log how long the alarm slept on which date."""

    with file(Alarm.LOG_PATH,"a") as f:
      f.write(str(date)+","+sleepTime)

  def logStop(time):
    """Write to the log how long it look for the alarm to stop."""

    with file(Alarm.LOG_PATH,"a") as f:
      f.write("stop:"+str(time))

  @staticmethod
  def main(argv)
  {
    a = Alarm(time, acclimate)
    a.startAlarm()
    a.stopAlarm()
  }
