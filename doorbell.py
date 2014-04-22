#!/usr/bin/python

import time

import button_bell_helper
import helper
import helper.status

class Doorbell(helper.HelperLoop):

  ADAPTER_URL = 'http://www:8080/status/doorbell'

  # We only send an external notification if there wasn't a button press for
  # at least this many seconds.
  NOTIFY_DELAY = 30

  def __init__(self):
    super(Doorbell, self).__init__()

    # Create helpers for serial/status communication.
    self.button_bell = button_bell_helper.Helper()
    self.status = helper.status.Helper(self.ADAPTER_URL)

    self.button_down = False
    self.button_last_pushed = None

    # Reset the adaptor values BEFORE starting helpers.
    self.status.update(self.create_empty_components(), blocking=True)

    # Register/start our helpers for the main loop.
    self.setup_helper(self.button_bell, self.handle_button_bell)
    self.setup_helper(self.status, self.handle_status)

  def create_empty_components(self):
    """Create an empty template for the status adapter we maintain."""
    return {
      'button': {'doorbell': {}},
      'bell': {'doorbell': {}},
    }

  def handle_button_bell(self, update):
    now = time.time()

    if update['button'] and not self.button_down:
      self.button_down = True
      self.button_last_pushed = now
      self.button_bell.connection.send(dict(ring=update['button']))
      self.status.push_button('doorbell')

    # Make the bell match the button.
    if update['button'] != update['ring']:
      self.button_bell.connection.send(dict(ring=update['button']))

  def handle_status(self, update):
    print "Status: %s" % update
    updated_status_value = update['status']

    # Recreate our adapter status is it's empty (ie: on monitor restart)
    if not updated_status_value:
      self.status.update(self.create_empty_components())

def main():
  Doorbell().run_forever()


if __name__ == "__main__":
  main()
