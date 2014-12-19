#!/usr/bin/python
from sys import argv
from os import system
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
    ACCLIMATE_LENGTH the length of acclimation time in seconds.
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
  ACCLIMATE_LENGTH = 5 * 60
  ACCELERATE_BEEPS = 10
  ACCELERATE_TIME = 1 * 60 * 60
  BEEP_INTERVAL = 1
  CODE_LENGTH = (4,8)
  LOG_PATH = "./.sleeplog"
  DICT_PATH = "/etc/dictionaries-common/words"

  def __init__(self, wakeupTime, acclimate=False, accelerate=False):
    """Initialize an Alarm given wakeup time and optional acclimate boolean."""

    self.wakeupTime = wakeupTime
    self.acclimate = acclimate
    self.accelerate = accelerate
    self._beeper = Beeper()
    self._logger = SleepLogger(self.LOG_PATH)

  @staticmethod
  def BEEP(frequency=-1):
    """Make the computer beep by the internal speaker with optional frequency.

    If no frequency is specified, the system default is used.
    The current implementation relies on system calls to beep.
    This method may need to be adjusted depending upon the system.

    """
    system("paplay /usr/share/sounds/ubuntu/stereo/message.ogg");
    #system("beep %s -e /dev/input/by-path/platform-pcspkr-event-spkr" % \
    #  ("" if (frequency == -1) else ("-f %i" %frequency)))

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

  def genPhrase(self):
    """Generate a string of random words used to shutoff the alarm.

    For the ith line in the dictionary, add it to a list of words with
    probability 1/i.

    """
    words = [""] * randint(*self.CODE_LENGTH)
    p = 1.0
    with file(self.DICT_PATH, "r") as f:
      for line in f.readlines():
        for i in xrange(len(words)):
          if random() < (1/p):
            words[i] = line.rstrip("\n")
        p += 1
    return " ".join(words)

  def startAlarm(self):
    """Start the alarm clock and sleep and start beeping when done.

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
    now = datetime.datetime.today()
    wait = (self.wakeupTime - now).total_seconds()
    self._logger.logStart(now)
    self._logger.logSleep(wait)
    if(self.accelerate and wait > self.ACCELERATE_TIME):
      Alarm.SLEEP(wait - self.ACCELERATE_TIME)
      wait -= (wait - self.ACCELERATE_TIME) #setup for acclimate
      for _ in xrange(self.ACCELERATE_BEEPS):
        Alarm.BEEP()
    if (self.acclimate and wait > self.ACCLIMATE_LENGTH):
      Alarm.SLEEP(wait - self.ACCLIMATE_LENGTH)
      for i in xrange(1,6):
        i = self.ACCLIMATE_PATTERN(i)#Reassign i so its value can be used
        Alarm.BEEP(4000*i)#Modulate the frequency
        Alarm.SLEEP(self.ACCLIMATE_LENGTH * i)
    else:
      self.SLEEP(wait)
    #Start beeping
    self.startBeeps()

  def stopAlarm(self):
    """Stop the alarm clock when the user enters the correct word sequence."""

    start = datetime.datetime.today()
    #Construct a phrase from a random number of random words in the dictionary
    stopCode = self.genPhrase()

    print self.SHUTOFF_MSG
    while raw_input("%s  %s\n  "%(stopCode, self.ANTI_COPY_MSG)) != stopCode:
      print(self.INCORRECT_MSG)
    self.stopBeeps()
    stop = datetime.datetime.today()

    self._logger.logStop((stop - start).total_seconds())
    self._logger.logLength(len(stopCode))
    self._logger.close()

  @staticmethod
  def main(argv):
    """Main method.

    If no time is given as an argument, accept input from the user.
    Create an alarm and start it to go off for the specified time.
    If given as an argument, create the alarm to make acclamitory beeps.

    """
    acclimate = ("-a" in argv)
    accelerate = ("-x" in argv)

    #Create a timestruct from user input if no argument was given
    timestruct = strptime((raw_input("Enter wakeup time in the format:" \
      " HH:MM ") if len(argv) < 2 else argv[1]),"%H:%M")

    today = datetime.datetime.today()
    time = datetime.datetime(today.year, today.month, today.day, \
      timestruct.tm_hour, minute = timestruct.tm_min)
    #If the time has happened already, assume its for tomorrow: add 1 day
    if today > time:
      time+=datetime.timedelta(1)

    a = Alarm(time, acclimate, accelerate)
    a.startAlarm()
    a.stopAlarm()

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

  """

  FORMAT = "{slept}#{start} {shutoff} {length}"

  def __init__(self, filePath):
    """Given a path to a log file, initialize a SleepLogger.

    This implementation doesn't actually open any files until close() is
    called.

    """
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

    with file(self.logPath, "a") as log:
      log.write(self.FORMAT.format( \
        slept = self.slept, \
        start = self.start, \
        shutoff = self.shutoff, \
        length = self.length))

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
