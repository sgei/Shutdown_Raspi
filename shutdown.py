#!/usr/bin/python
# shutdown Raspberry Pi via button

import RPi.GPIO as GPIO
import subprocess, time, sys, syslog, threading
from sgei_gpio import OUT_BLINK

IN_PORT = 23        # Input Shutdown-Button
LED1 = None         # yellow LED object (Shutdown-LED)
LED1_PORT = 25      # GPIO-BCM Port
LED1_TIME = 0.2     # ON/OFF time for LED flashing
STATE = 0           # program state
T1 = None           # timer object for first press duration
T1_TIME = 0.5       # timer time
T2 = None           # timer object for LED flashing time
T2_TIME = 3.0       # timer time

# Initialize GPIO, BMC pin number
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(IN_PORT, GPIO.IN)
GPIO.setup(LED1_PORT, GPIO.OUT)

# initial output value
GPIO.output(LED1_PORT, GPIO.LOW)

def t1_action():
  global STATE, LED1, LED1_PORT, LED1_TIME

  STATE = 2
  LED1 = OUT_BLINK(LED1_PORT, LED1_TIME)
  LED1.start()

def t2_action():
  global STATE, LED1

  STATE = 0
  if not LED1 is None:
    LED1.stop()

# Interrupt routine for shutdown button
def buttonISR(pin):
  global STATE, LED1, T1, T2, T1_TIME, T2_TIME

  # button pressed
  if (GPIO.input(pin)):

    PRESSED = 1

    if (STATE == 0) and (PRESSED == 1):
      STATE = 1
      PRESSED = 0

      T1 = threading.Timer(T1_TIME, t1_action)
      T1.start()

    if (STATE == 2) and (PRESSED == 1):
      STATE = 3
      PRESSED = 0

      if not T2 is None:
        T2.cancel()

  # button released
  else:
    if STATE == 1:
      if not T1 is None:
        T1.cancel()
      STATE = 0

    if STATE == 2:
      T2 = threading.Timer(T2_TIME, t2_action)
      T2.start()

  if STATE == 3:

    if not LED1 is None:
      LED1.stop()

    STATE = 0
    GPIO.output(LED1_PORT, GPIO.HIGH)

    #print "Shutdown..."
    syslog.syslog('Shutdown: System halted');
    subprocess.call(['shutdown', '-h', 'now'], shell=False)

# Switch on the interrupt for the shutdown button
GPIO.add_event_detect(IN_PORT, GPIO.BOTH, callback=buttonISR)

syslog.syslog('Shutdown.py started');
while True:
  try:
    time.sleep(300)
  except KeyboardInterrupt:

    if not LED1 is None:
      LED1.stop()

    GPIO.cleanup()

    syslog.syslog('Shutdown terminated (Keyboard)');
    print ("\nBye")
    sys.exit(0)