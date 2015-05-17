#!/usr/bin/python
from sys import argv
from subprocess import call
from time import sleep, strptime
from random import randint, choice, random
import threading, datetime

class Alarm(object):
  """Alarm object that, given a time to wakeup, can sleep and then beep.

  Shutting off the alarm requires the user to input a generated sequence
  of dictionary words. Relevant data is logged throughout the process.

  Class Variables:
    SLEEP_MSG tuple containing possible messages to display once activated.
    INCORRECT_MSG string to display when shutoff input does not match.
    SHUTOFF_MSG string to display when user is prompted to shutoff alarm.
    ANTI_COPY_MSG string that is invisible and affects terminal copying.
    BEEP_INTERVAL number of seconds between alarm beeps beeps.
    CODE_LENGTH tuple defining a lower and upper bounds for the code length.
    LOG_PATH path for the log file.
    DICT_PATH path for the dictionary used for the deactivation code.

  Member Variables:
    wakeupTime datetime object for when the alarm is set to go off.
    acclimate boolean indicating if the alarm should make acclamitory beeps.
    _beeper Beeper instance for beeping on a separate thread.
    _logger SleepLogger instance used to log data to LOG_PATH.

  """

  SLEEP_MSG = ("Sweet Dreams","Goodnight")
  INCORRECT_MSG = "incorrect input"
  SHUTOFF_MSG = "Enter the following to terminate alarm:"
  ANTI_COPY_MSG = " "
  CODE_LENGTH = (4,8)
  LOG_PATH = "./.sleeplog"
  DICT_PATH = "/etc/dictionaries-common/words"

  def __init__(self, wakeupTime, events, noLog=False):
    """Initialize an Alarm given a time to wake up and a list of SleepEvents.

    `wakeupTime' should be an instance of a datetime.

    `events' must be a Python list of SleepEvent subclass instanced of to occur
    during the period slept when goToSleep() is called.

    `noLog' optional boolean specifies if data from this alarm should be
    logged; by default it is. This is useful to exclude abnormal usages from
    the log.

    """
    self.wakeupTime = wakeupTime
    self._beeper = Beeper()
    self._logger = SleepLogger(self.LOG_PATH, noLog)
    self.events = events

  def soundAlarm(self):
    """Start a beep thread and beep until _stopAlarm is called."""

    print "soundAlarm()"
    return
    self._beeper.start()

  def _stopAlarm(self):
    """Stop the beep thread."""

    self._beeper.stop()

  def genPhrase(self):
    """Generate a string of random words used to shutoff the alarm.

    For the ith line in the dictionary, add it to a list of words with
    probability 1/i.

    """
    words = [""] * randint(*self.CODE_LENGTH)
    p = 1
    with file(self.DICT_PATH, "r") as f:
      for line in f.readlines():
        for i in xrange(len(words)):
          if random() < (1.0/p):
            words[i] = line.rstrip("\n")
        p += 1
    return " ".join(words)

  def goToSleep(self):
    """Start the alarm clock by going to sleep and then activating the alarm.

    The procedure:
    Display a random sleep message to the user. Compute the number of
    seconds between the time the alarm is started and the time to wakeup.
    Log when the user goes to sleep and wait. If acclamitory beeps are
    enabled, wait for less time and then make occasional beeps, waiting
    in-between. When its time for the user to wake-up, start a beeping
    thread.

    """
    #Print sleep message
    print(choice(self.SLEEP_MSG))
    alarmStart = datetime.datetime.today()
    wait = (self.wakeupTime - alarmStart).total_seconds()
    print wait
    self._logger.logStart(alarmStart)
    self._logger.logSleep(wait)

    #Construct a phrase from a random number of random words in the dictionary
    stopCode = self.genPhrase()

    #for each subclass, inform it of the sleep length
    for e in self.events:
      e.setSleepLength(wait)
    self.events.sort()
    print self.events

    #activate each of the events in the order they occur
    for e in self.events:
      timeLeft = e.getTime() - \
        (datetime.datetime.today() - alarmStart).total_seconds()
      if timeLeft > 0:
        sleep(timeLeft)
        e.event()

    #sleep the remaining amount of time
    timeLeft = (self.wakeupTime - datetime.datetime.today()).total_seconds()
    if timeLeft > 0:
      sleep(timeLeft)

    #Start beeping
    self.soundAlarm()

    print self.SHUTOFF_MSG
    #while raw_input("%s  %s\n  " % (stopCode, self.ANTI_COPY_MSG)) != stopCode:
    #  print(self.INCORRECT_MSG)
    self._stopAlarm()

    self._logger.logStop( \
      (datetime.datetime.today() - self.wakeupTime).total_seconds())
    self._logger.logLength(len(stopCode))
    self._logger.close()

  @staticmethod
  def main(argv):
    """Main method given an argument vector, parse it and start an Alarm.

    If no time is given as an argument, accept input from the user.
    Create an alarm and start it to go off for the specified time.
    If given as an argument, create the alarm to make acclamitory beeps.

    """
    #Create a timestruct from user input if no argument was given
    timestruct = strptime((raw_input("Enter wakeup time in the format:" \
      " HH:MM ") if len(argv) < 2 else argv[1]),"%H:%M")

    today = datetime.datetime.today()
    time = datetime.datetime(today.year, today.month, today.day, \
      timestruct.tm_hour, minute = timestruct.tm_min)
    #If the time has happened already, assume its for tomorrow: add 1 day
    if today > time:
      time+=datetime.timedelta(1)

    #parse the options to construct the events list
    events = []
    if "-a" in argv:
      events.append(AcclimateEvent())
    if "-x" in argv:
      events.append(AccelerateEvent())

    Alarm(time, events, "-n" in argv).goToSleep()

class SleepLogger(object):
  """Logger class specialized for logging sleep pattern data.

  This class uses a template for formatting the relative positions of output
  data, but currently, the formats of individual fields can be anything.

  close() must be called to ensure the data logged is actually written out.

  The current implementation only saves the most recently logged data and only
  writes to the log file if close() is called. It will error if not all the
  logging methods are called: there are no default fields.

  Class Variables:
    FORMAT string for formatting the log output.
      slept units of time spent sleeping.
      start date that the alarm was started.
      shutoff units of time spent shutting off the alarm.
      length the length of the string, in units, needed to stop the alarm.

  Member Variables:
    filePath the file path to the persistent log file.
    noPersist boolean indicating if logged entries should be flushed to disk.
    slept number of hours slept for a single entry.
    start datetime the alarm was started.
    shutoff the number of seconds needed to shutoff the alarm.
    length the length, in characters, of the alarm shutoff code.
  """

  FORMAT = "{slept}#{start} {shutoff} {length}\n"

  def __init__(self, filePath, noPersist=False):
    """Given a path to a log file, initialize a SleepLogger.

    noPersist optional boolean indicating whether entries should be written to
    disk.

    This implementation doesn't actually open any files until close() is
    called.

    """
    self.noPersist = noPersist
    self.logPath = filePath

  def logSleep(self, timeSlept):
    """Write to the log the amount of time spent sleeping.

    logSleep() expects timeSlept to be in seconds and formats it to hours for
    the log.

    """
    self.slept = timeSlept/3600

  def logStart(self, start):
    """Write to the log the time that the alarm was started.

    Currently there is no requirement for the formatting of start.

    """
    self.start = start

  def logStop(self, stop):
    """Write to the log how long it look for the alarm to stop."""

    self.shutoff = stop

  def logLength(self, length):
    """Write to the log how long a string was needed to shutoff the alarm."""

    self.length = length

  def close(self):
    """Ensure that the data logged is written out to the log file."""

    if self.noPersist: #don't write any non-persistent data
      return
    with file(self.logPath, "a") as log:
      log.write(self.FORMAT.format( \
        slept = self.slept, \
        start = self.start, \
        shutoff = self.shutoff, \
        length = self.length))

class SleepEvent():
  """Abstract class representing phenomena to occur during the sleep time.

  setSleepLength() should be called before any other method.

  Subclasses should override setSleepLength(), getTime(), and event().

  """

  def setSleepLength(self, wait):
    """Set the total sleep time as it may alter the behaviour of the event."""

    raise NotImplementedError()

  def getTime(self):
    """Return the amount of time until the event is to occur.

    If the event cannot occur for any reason, return 0.

    """
    raise NotImplementedError()

  def event(self):
    """Callback to make the event occur after getTime() has elapsed.

    If the event cannot occur for any reason, event() should be a nop.

    """
    raise NotImplementedError()

  def __lt__(self, rhs):
    """Return whether self is sooner than rhs, the right hand side.

    self.getTime() < rhs.getTime().

    """
    return self.getTime() < rhs.getTime()

  def __eq__(self, rhs):
    """Return whether self is at the same time as rhs, the right hand side.
    
    self.getTime() == rhs.getTime().
    
    """
    return self.getTime() == rhs.getTime()

  def __le__(self, rhs):
    """Return whether self <= rhs."""

    return (self < rhs) or (self == rhs)

  def __ne__(self, rhs):
    """Return whether self != rhs."""

    return not (self == rhs)

  def __gt__(self, rhs):
    """Return whether self > rhs."""

    return not (self <= rhs)

  def __ge__(self, rhs):
    """Return whether self >= rhs."""

    return (self > rhs) or (self == rhs)

class AcclimateEvent(SleepEvent):
  """AclimateEvent extends SleepEvent to make acclamitory beeps during sleep.

  The idea behind this event is that non-period sounds should be played prior
  to the completion of the entire sleep period to ease the process of waking
  up. This may help reduce fatigue and the desire to go back to sleep after the
  alarm is shut off.

  Class Variables:
    PERIOD the length, in seconds, before the end of the sleep period to start
      the acclimation period.
    ITERATIONS the number of iterations that the acclimation pattern should be
      called.

  Member Variables:
    pattern function to call on the ith iteration of ITERATIONS to determine
      how long to sleep.

  """

  PERIOD = 5 * 60
  ITERATIONS = 5

  def __init__(self, pattern=None):
    """Initialize an AcclimateEvent given the length of the acclimation period
    and optional pattern.

    """
    self.pattern = staticmethod(pattern) if pattern else \
      AcclimateEvent.defaultPattern

  @staticmethod
  def defaultPattern(i):
    """Return the ith number in a particular exponential regression."""

    return .5274 * (i**(-1.5214))

  def acclamitoryBeep(self):
    """Beep the computer's speaker for an acclamitory beep.

    Override this method to change which sounds are played.

    """
    defaultBeep()

  def setSleepLength(self, wait):
    """Set the total sleep period time."""

    self.wait = wait - self.PERIOD

  def getTime(self):
    """Return the time until the acclimation period."""

    if self.wait < 0:
      return 0
    return self.wait

  def event(self):
    """Start the acclimation period.

    Beep and call pattern to determine how much to sleep in between.

    If getTime() returns 0, then event() should act as a nop; otherwise, 
    event() should block for at most PERIOD seconds.

    """
    print "AcclimateEvent event()"
    if not self.getTime():
      return

    for i in xrange(1, self.ITERATIONS+1):
      self.acclamitoryBeep()
      sleep(self.PERIOD * self.pattern(i))

class AccelerateEvent(SleepEvent):
  """AccelerateEvent extends SleepEvent to beep some time prior to waking up.

  The idea behind this event is that suddenly waking up some time before the
  main alarm followed by immediate sleep leads to accelerated REM sleep.

  Class Variables:
    PERIOD the length, in seconds, before the end of the sleep period to start
      the acclimation period.
    ITERATIONS the number of times to beep when event is called.

  """

  PERIOD = 1 * 60 * 60
  ITERATIONS = 6

  def beep(self):
    """Beep the computer's speaker."""

    defaultBeep()

  def setSleepLength(self, wait):
    """Set the total sleep period time."""

    self.wait = wait - self.PERIOD

  def getTime(self):
    """Return the time until the acclimation period."""

    if self.wait < 0:
      return 0
    return self.wait

  def event(self):
    """Start the acceleration period.

    Beep and call pattern to determine how much to sleep in between.

    If getTime() returns 0, then event() should act as a nop; otherwise, 
    event() should beep ITERATIONS times.

    """
    print "AccelerateEvent event()"
    if not self.getTime():
      return

    for i in xrange(self.ITERATIONS):
      self.beep()

class Beeper(threading.Thread):
  """Beeper object that beeps on another thread until stopped.

  Subclasses Thread and overrides the run method to periodically beep. The
  beeping thread is started by calling run() and stopped by a call to stop().
  Once stop() is called, run() has no effect.

  Class Variables:
    BEEP_INTERVAL the number of seconds to wait between beeping.

  Member Variables:
    _beep boolean indicating if the Beeper should beep.
      Call stop() to set this to False and terminate the thread.

  """

  BEEP_INTERVAL = 1

  def __init__(self):
    """Initialize a Beeper."""

    threading.Thread.__init__(self, None, None, None, (), {})
    self._beep = True

  @staticmethod
  def beep():
    """Make the computer beep the internal speaker."""

    defaultBeep()

  def run(self):
    """Beep and wait a certain interval until stop() is called."""

    while self._beep:
      Beeper.beep()
      sleep(self.BEEP_INTERVAL)

  def stop(self):
    """Stop the beeping thread.

    If the Beeper is not currently beeping,
    calls to run() will have no effect.

    """
    self._beep = False

def defaultBeep():
  """Cause the computer to make some noise that will likely wake the user."""

  call(("/usr/bin/paplay", "/usr/share/sounds/ubuntu/stereo/message.ogg"))

#mock out for testing
def sleep(t):
  print t
defaultBeep = lambda : None

#Execute the main method
if __name__ == "__main__":
  Alarm.main(argv)
