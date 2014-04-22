
import json
import multiprocessing
import os
import time

import requests

import helper

class Helper(helper.HelperBase):
  """Mirror of Web API of Status structure.

  Process reads the full remote status struct, and communicates back updates.

  Other methods provide non-blocking ways to write to that structure.
  """

  def __init__(self, adapter_url):
    super(Helper, self).__init__()
    self.adapter_url = adapter_url
    self._pool = multiprocessing.Pool(1)

  def run(self):
    revision = None

    while True:
      try:
        r = requests.get(self.adapter_url, params={'revision': revision})
        if r:
          rj = r.json()
          revision = rj['revision']
          self._connection.send(rj)

      except requests.ConnectionError:
        # If we got an error back from the server, wait a bit and try again.
        print 'Got a ConnectionError. Retrying shortly.'
        time.sleep(5)

  def update(self, value, sub_path='', revision=None, blocking=False):
    """Update a component value owned by this process.
    """
    if sub_path:
      update_url = os.path.join(self.adapter_url, sub_path)
    else:
      update_url = self.adapter_url

    params = {}
    if revision is not None:
      params['revision'] = revision

    headers = {'content-type': 'application/json'}
    json_value = json.dumps(value)

    print "PUT: %s" % update_url
    if blocking:
      requests.put(update_url, params=params, headers=headers, data=json_value)
    else:
      self._pool.apply_async(
          requests.put,
          (update_url,), dict(params=params, headers=headers, data=json_value))

  def push_button(self, button):
    """Helper for marking a button component pushed."""
    print "Push: %s" % button
    sub_path = os.path.join('button', button, 'pushed')
    now = int(time.time())
    self.update(now, sub_path)
