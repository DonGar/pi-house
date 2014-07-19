#!/usr/bin/python

import button_bell_helper
import helper
import helper.status

class Doorbell(helper.HelperLoop):

  ADAPTER_URL = 'http://www:8080/status/doorbell'

  def __init__(self):
    super(Doorbell, self).__init__()

    # Create helpers for serial/status communication.
    self.button_bell = button_bell_helper.Helper()
    self.status = helper.status.Helper(self.ADAPTER_URL)

    # Remember the current status of the button push.
    self.button_down = False

    # Reset the adaptor values BEFORE starting helpers.
    self.create_empty_components()

    # Register/start our helpers for the main loop.
    self.setup_helper(self.button_bell, self.handle_button_bell)
    self.setup_helper(self.status, self.handle_status)

  def create_empty_components(self):
    """Create an empty template for the status adapter we maintain."""
    components = {
        'button': {'doorbell': {}},
        'bell': {'doorbell': {}},
        }
    self.status.update(components, blocking=True)

  def handle_button_bell(self, update):
    if update['button'] and not self.button_down:
      self.status.push_button('doorbell')

    self.button_down = update['button']

    # Make the bell match the button.
    if update['button'] != update['ring']:
      self.button_bell.connection.send(dict(ring=update['button']))

  def handle_status(self, update):
    print "Status: %s" % update

    if not update:
      self.create_empty_components()
      return

    updated_status_value = update['status']

    # Recreate our adapter status if it's empty (ie: on monitor restart)
    if not updated_status_value:
      self.create_empty_components()
      return

def main():
  Doorbell().run_forever()


if __name__ == "__main__":
  main()
