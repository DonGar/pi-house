#!/usr/bin/python

import time

import RPi.GPIO as GPIO

import helper

# Which GPIO pins are used to detect a button press, or to ring the bell.
BUTTON = 7 # GPIO4
BELL = 11  # GPIO 17


class Helper(helper.HelperBase):
  """Watches for doorbell pushes, and controls bell ring."""

  MAX_RING_TIME = 10

  def __init__(self):
    super(Helper, self).__init__()

    self.button_down = False
    self.ring = False

    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    GPIO.setup(BUTTON, GPIO.IN)
    GPIO.setup(BELL, GPIO.OUT)

  def run(self):
    while True:
      send_status = False

      # BUTTON reads low when pushed, high when up.
      read_down = not GPIO.input(BUTTON)

      # If the doorbell changed state.
      if read_down != self.button_down:
        self.button_down = read_down
        print "Button is %s" % read_down
        send_status = True

      # If we received a control message.
      if self._connection.poll():
        msg = self._connection.recv()
        self.ring = msg['ring']
        GPIO.output(BELL, msg['ring'])

        send_status = True

      # If anything might have changed.
      if send_status:
        msg = dict(button=self.button_down, ring=self.ring)
        self._connection.send(msg)

      # Sleep a little, saves a lot of power.
      time.sleep(0.05)
