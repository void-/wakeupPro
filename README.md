wakeupPro
=========
Alarm clock in Python.

Given a time, calculate the difference between now and that time. Wait until
that time, then activate an alarm. To deactivate the alarm, the user must 
correctly enter the random string that is printed to the screen.

Additional features:
* Option for an acclamitory beep
    - The alarm will make an exponential regression of beeps at varying
    - frequencies to make waking up a more gradual process.
* Logging
    - Logs how long the alarm sleeps on a certain day.
    - It also logs how long it takes for the alarm to be shut off for a metric
      of fatigue.
