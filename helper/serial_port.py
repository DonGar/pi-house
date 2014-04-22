
import serial
import time

import helper

class Helper(helper.HelperBase):
  """Talk over the serial port."""

  def __init__(self, serial_port):
    super(Helper, self).__init__()
    self._serial_port = serial_port

  def run(self):
    # Outer loop iterates if the serial connection is lost and reconnects.
    # This usually indicates the arduino was disconnected and reconnected.
    while True:
      try:
        with serial.Serial(self._serial_port, 115200, timeout=0.1) as s:

          while True:
            # This read will timeout if there is nothing to read.
            msg = s.readline().strip()
            if msg:
              self._connection.send(msg)

            if self._connection.poll():
              msg = self._connection.recv()
              s.write(bytes(msg))

      except serial.SerialException:
        print 'Serial connection lost, retrying....'
        time.sleep(1)
