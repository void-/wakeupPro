from sys import argv
from os import system
from time import sleep, strptime
from random import randint, choice
import threading, datetime

class Alarm(object):
  """Alarm object that, given a time to wakeup, can sleep and then beep.
  
  Class Variables:
    SLEEP_MSG tuple containing possible messages to display once activated.
    ACCLIMATE_LENGTH the length of acclimation time in seconds.
    BEEP_INTERVAL the number of seconds between alarm beeps beeps.
    CODE_LENGTH tuple defining a lower and upper bounds for the code length.
    LOG_PATH the path for the log file.
    DICT_PATH the path for the dictionary used for the deactivation code.

  Member Variables:
    wakeupTime datetime object for when the alarm is to beep.
    acclimate boolean indicating if the alarm should make acclamitory beeps.
    _beeper Beeper instance for beeping on a separate thread.
    _dict python dictionary with words from DICT_PATH.
    
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
    """Make the computer beep by the internal speaker.
    
    The current implementation relies on system calls to beep.
    This method may need to be adjusted depending upon the system.
    """

    system("beep -e /dev/input/by-path/platform-pcspkr-event-spkr")

  @staticmethod
  def SLEEP(seconds):
    """Sleep for a given number of seconds without using cpu."""

    sleep(seconds)

  @staticmethod
  def ACCLIMATE_PATTERN(iteration):
    """Return a number in an exponential regression for a given iteration."""

    return .5274 * (iteration**(-1.5214))

  def startBeeps(self):
    """Start a beep thread and beep until stop is called."""

    self._beeper.start()

  def stopBeeps(self):
    """Stop the beep thread."""

    self._beeper.stop()

  def loadDict(self):
    """Load all entries fom DICT_PATH into _dict and remove newlines."""

    with file(self.DICT_PATH, "r") as f:
      i = 0
      for line in f.readlines():
        self._dict[i] = line.rstrip("\n")
        i+=1

  def startAlarm(self):
    """Start the alarm clock and sleep and start beeping when done."""

    #Print sleep message
    print(choice(self.SLEEP_MSG))
    now = datetime.datetime.today() 
    wait = (self.wakeupTime - now).total_seconds()
    self.logSleep(now, wait)
    if self.acclimate and wait > Alarm.ACCLIMATE_LENGTH: 
      Alarm.SLEEP(wait - Alarm.ACCLIMATE_LENGTH)
      for i in xrange(1,6):
        Alarm.BEEP()
        Alarm.SLEEP(Alarm.ACCLIMATE_LENGTH * Alarm.ACCLIMATE_PATTERN(i))
    else:
      self.SLEEP(wait)
    #Start beeping
    self.startBeeps()

  def stopAlarm(self):
    """Stop the alarm clock when the user enters the correct word sequence."""

    start = datetime.datetime.today()
    self.loadDict() #load the dictionary
    stopCode = " ".join(self._dict[randint(0, len(self._dict))-1] \
      for _ in xrange(randint(*Alarm.CODE_LENGTH)))

    while raw_input(stopCode+"\n") != stopCode:
      print("incorrect input")
    self.stopBeeps()
    stop = datetime.datetime.today()
    #mark dictionary for garbage collection
    self._dict = None 
    self.logStop((stop - start).total_seconds())

  def logSleep(self, date, sleepTime):
    """Write to the log how long the alarm slept on which date.
    
    Given a datetime object and the number of seconds slept, write
    to the log in the following format:
      YYYY-MM-DD HH:MM:SS.SSSSSS, #ofSeconds\n
    Ex.:
      2013-07-06 13:21:12.632746, 10856
    
    """
    with file(self.LOG_PATH,"a") as f:
      f.write(str(date)+", "+str(sleepTime)+"\n")

  def logStop(self, time):
    """Write to the log how long it look for the alarm to stop.
    
    Given a floating point number representing the number of seconds it took
    for the alarm to stop, write it to the log in the following format:
      stop: #\n

    """

    with file(self.LOG_PATH,"a") as f:
      f.write("stop: "+str(time)+"\n")

  @staticmethod
  def main(argv):
    """Main method."""

    acclimate = False
    if " -a " in argv:
      acclimate = True

    timestruct = strptime((raw_input("Enter wakeup time in the format: HH:MM ")\
      if len(argv) < 2 else argv[1]),"%H:%M")

    today = datetime.datetime.today()
    time = datetime.datetime(today.year, today.month, today.day, \
      timestruct.tm_hour, minute = timestruct.tm_min)
    #if the time has happened already, assume its for tomorrow
    if timestruct.tm_hour < today.hour and timestruct.tm_min < today.minute:
      time+=datetime.timedelta(1)

    a = Alarm(time, acclimate)
    a.startAlarm()
    a.stopAlarm()

class Beeper(threading.Thread):
  """Beeper object that beeps on another thread until stopped.
  
  Subclasses Thread and overrides the run method to beep. The
  beeping thread is started by calling run() and stopped by
  a call to stop(). Once stop() is called, run() has no effect.

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
    """Stop the beeping thread.
    
    If the Beeper is not currently beeping,
    calls to run() will have no effect.
    """

    self._beep = False

#Execute the main method
if __name__ == "__main__":
  Alarm.main(argv)
