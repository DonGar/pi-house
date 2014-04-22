#!/usr/bin/python

import json
import os
import re

import helper.status
import helper.serial_port

class Control(helper.HelperLoop):
  SERIAL_PORT = '/dev/ttyUSB0'
  ADAPTER_URL = 'http://www:8080/status/control'

  BUTTONS = ('block_2',
             'block_1',
             'block_4',
             'block_3',
             'desktop_doorbell',
             'black',
             'red')

  RGBS = ('block_2_backlight',
          'block_1_backlight',
          'block_4_backlight',
          'block_3_backlight')

  # Matches: '0,0,0' '1, 1, 1', etc.
  COLOR_RE = re.compile(r'^[01], ?[01], ?[01]$')

  def __init__(self):
    super(Control, self).__init__()

    # Are buttons currently pushed down?
    self.button_state = [False] * len(self.BUTTONS)

    # What colors we are displaying?
    self.color_state = ['0,0,0'] * len(self.RGBS)

    # Create helpers for serial/status communication.
    self.serial = helper.serial_port.Helper(self.SERIAL_PORT)
    self.status = helper.status.Helper(self.ADAPTER_URL)

    # Reset the adaptor values BEFORE starting helpers.
    self.status.update(self.create_empty_components(), blocking=True)

    # Register/start our helpers for the main loop.
    self.setup_helper(self.serial, self.handle_serial_read)
    self.setup_helper(self.status, self.handle_status_read)

  def validate_color(self, color):
    if not self.COLOR_RE.match(color):
      raise ValueError("Bad color format.", color)

  def create_empty_components(self):
    """Create an empty template for the status helper we maintain.

    This really means an empty dictionary for each component. Buttons
    will have addtional values filled in remotely when they are pushed.
    RGBs will have their current color filled in as soon as we read them
    from the serial port.
    """
    rgbs = {}

    # Fill in current color information.
    for i in xrange(len(self.RGBS)):
      rgbs[self.RGBS[i]] = {'color': self.color_state[i]}

    return {
      'button': {button: {} for button in self.BUTTONS},
      'rgb': rgbs,
    }

  def update_status_color(self, component, color):
    """Update the current color value for an RGB component.

    Args:
      component: The name of the component (ex: 'block_2_backlight').
      color: The new color value. "RGB" where RGB are 0 or 1 (on/off)
    """
    # Color should be a string of the form:  "0,0,0", "1, 0, 1", etc.
    sub_path = os.path.join('rgb', component, 'color')
    self.status.update(color, sub_path=sub_path)

  def update_serial_color(self, colors):
    """Notify the serial helper to update all background colors.

    Args:
      colors: The new colors. ["R,G,B" where RGB are 0 or 1 (on/off)
    """
    assert len(colors) == len(self.RGBS)
    for color in colors:
      self.validate_color(color)

    # ['1,1,1', '0,0,0', '0, 0, 0', '0, 0, 0'] -> '000:000:000:000'
    update_string = ':'.join(colors).replace(',', '').replace(' ', '')

    print 'Serial send: %s' % update_string
    self.serial.connection.send(update_string)

  def handle_status_read(self, update):
    # update format like:
    #   {u'status': {},
    #    u'url': u'http://www:8081/status/control',
    #    u'revision': 3}
    print "Status: %s" % update
    updated_status_value = update['status']

    # Recreate our adapter status is it's empty (ie: on monitor restart)
    if not updated_status_value:
      self.status.update(self.create_empty_components())

    rgb_components = updated_status_value.get('rgb', {})

    # Look for new target colors to update our RGBs too.
    new_colors = self.color_state[:]

    for i in xrange(len(self.RGBS)):
      component = rgb_components.get(self.RGBS[i], {})
      target = component.get('target', None)
      if target:
        # Clear target value.
        sub_path = os.path.join('rgb', self.RGBS[i], 'target')
        self.status.update(None, sub_path=sub_path, revision=update['revision'])

        # Validate target.
        self.validate_color(target)
        new_colors[i] = target

    # If we aren't already using the target colors, update!
    if new_colors != self.color_state:
      self.update_serial_color(new_colors)

  def handle_serial_read(self, update):
    print "Serial: %s" % update
    msg = json.loads(update)

    # Handle possible button changes.
    updated_buttons = msg['buttons']
    for i in xrange(len(self.BUTTONS)):
      if updated_buttons[i] and updated_buttons[i] != self.button_state[i]:
        print 'Button %s pushed.' % self.BUTTONS[i]
        self.status.push_button(self.BUTTONS[i])
    self.button_state = updated_buttons

    # Read color values.
    updated_colors = msg['colors']
    for i in xrange(len(self.RGBS)):
      if updated_colors[i] != self.color_state[i]:
        self.color_state[i] = updated_colors[i]
        self.update_status_color(self.RGBS[i], updated_colors[i])


def main():
  Control().run_forever()


if __name__ == "__main__":
  main()
