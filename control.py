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

    # What colors are we switching too?
    self.target_colors = ['0,0,0'] * len(self.RGBS)

    # Create helpers for serial/status communication.
    self.serial = helper.serial_port.Helper(self.SERIAL_PORT)
    self.status = helper.status.Helper(self.ADAPTER_URL)

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

    components = {
        'button': {button: {} for button in self.BUTTONS},
        'rgb': rgbs,
        }
    self.status.update(components, blocking=True)

  def verify_status_update(self, update):
    if not update:
      return False

    updated_status_value = update.get('status', {})
    if not updated_status_value:
      return False

    button_components = updated_status_value.get('button', {})
    if not set(button_components.keys()) == set(self.BUTTONS):
      return False

    rgb_components = updated_status_value.get('rgb', {})
    if not set(rgb_components.keys()) == set(self.RGBS):
      return False

    return True

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
    #   {u'status': {...},
    #    u'url': u'http://www:8081/status/control',
    #    u'revision': 3}

    # Recreate our adapter status if it doesn't verify (server restart, etc)
    if not self.verify_status_update(update):
      self.create_empty_components()
      return

    # Look for new target colors to update our RGBs too.
    orig_targets = self.target_colors[:]

    for i in xrange(len(self.RGBS)):
      target = update['status']['rgb'][self.RGBS[i]].get('color_target', None)
      if target:
        # Clear target value.
        sub_path = os.path.join('rgb', self.RGBS[i], 'color_target')
        self.status.update(None, sub_path=sub_path, revision=update['revision'])

        # Validate target.
        self.validate_color(target)
        self.target_colors[i] = target

    # If we aren't already using the target colors, update!
    if orig_targets != self.target_colors:
      self.update_serial_color(self.target_colors)

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
