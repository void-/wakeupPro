wakeupPro
=========
Alarm clock in Python.

Given a time, calculate the difference between now and that time. Wait until
that time, then activate an alarm. To deactivate the alarm, the user must
correctly enter the random string that is printed to the screen.

Examples
---------
Wake up at 07:00 with acclamitory beeps.
```bash
$ ./wakeupPro.py 7:00 -a
```
Take a nap until 14:45 without logging any data.
```bash
$ ./wakeupPro.py 14:45 -n
```

Additional features:
* Option for an acclamitory beep (-a)
    - The alarm will make an exponential regression of beeps at varying
      frequencies to make waking up a more gradual process.
* Option for accelerated sleep (-x)
    - The alarm will beep a number of times 1 hour before the user is to wake
      up but not require it to be shut off. This can lead to accelerated REM
      sleep.
* Anti copy-paste mechanism
    - The output random string cannot be directly copied and pasted to shut off
      the alarm.
* Logging
    - Logs how long the alarm sleeps on a certain day.
    - It also logs how long it takes for the alarm to be shut off for a metric
      of fatigue.
    - Option for no logging (-n).
* Extensible
    - New options can be easily added by subclassing SleepEvent.

Graphing
--------
Graphing the number of hours slept each day is intended to be very simple. To
graph other data, more complicated parsing needs to be done.

To simply graph the number of hours slept over time as logged by wakeupPro, run
```bash
$ graph -T X -a .sleeplog
```
For a better looking graph, try
```bash
$ graph -T X --bitmap-size 1024x1024 -a -S 3 .sleeplog
```

To graph the amount of time it took to shut off the alarm each day(as some
metric of fatigue), try
```bash
$ grep .sleeplog -o -P -e " [0-9.]+ " | graph -T X --bitmap-size 1024x1024 -a -S 3
```
