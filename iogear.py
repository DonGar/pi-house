#!/usr/bin/python

import helper.status
import helper.serial_port

class IoGear(helper.HelperLoop):
  SERIAL_PORT = '/dev/ttyACM0'
  ADAPTER_URL = 'http://www:8080/status/iogear/iogear/desktop'

  def __init__(self):
    super(IoGear, self).__init__()

    # Create helpers for serial/status communication.
    self.serial = helper.serial_port.Helper(self.SERIAL_PORT)
    self.status = helper.status.Helper(self.ADAPTER_URL)

    # Reset the adaptor values BEFORE starting helpers.
    self.status.update(self.create_empty_components(), blocking=True)

    # Send an initial query over the serial line to find out the current port.
    self.serial.connection.send('?')

    # Register/start our helpers for the main loop.
    self.setup_helper(self.serial, self.handle_serial_read)
    self.setup_helper(self.status, self.handle_status_read)

  def create_empty_components(self):
    """Create an empty template for the status helper we maintain.

    The adaptor cotains a component named 'desktop', of type 'iogear'.
    Values on the component will be filled in when available.
    """
    return {'active': None}

  def handle_status_read(self, update):
    # update format like:
    #   {u'status': {...},
    #    u'url': u'http://www:8081/status/iogear/iogear/desktop',
    #    u'revision': 27}
    desktop_component = update['status']

    # Recreate our adapter status is it's empty (ie: on server restart)
    if not desktop_component:
      self.status.update(self.create_empty_components())
      return

    # Target is expected to be an integer 0 <= target <= 3. We don't validate,
    # just pass along.
    target = desktop_component.get('active_target', None)

    if target:
      # Send the new target over the serial line.
      self.serial.connection.send(target)

      # Clear the target value. If it's updated before we clear it, the revision
      # will protect the new value.
      self.status.update(
          None, sub_path='active_target', revision=update['revision'])

  def handle_serial_read(self, update):
    # Update is expected to be an integer 0 <= target <= 3. We don't validate,
    # just pass along.
    print "Serial: %s" % update
    self.status.update(update.strip(), sub_path='active')


def main():
  IoGear().run_forever()


if __name__ == "__main__":
  main()
