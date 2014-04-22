
import multiprocessing
import select
import traceback

class HelperBase(multiprocessing.Process):
  """This class performs IO in a different process to avoid blocking.

  It uses a multiprocessing.Connection to communicate back to the main loop
  since that object provides a FD compatible with select calls.
  """
  def __init__(self):
    super(HelperBase, self).__init__()
    a, b = multiprocessing.Pipe()

    # Connection for the control process to use.
    self.connection = a

    # Connection for the local process to use.
    self._connection = b

  def run(self):
    assert False, "Not implemented."


class HelperLoop(object):
  """This class creates an event loop for classes that extend HelperBase.

  To use it, call setup_helper whenever you want to add a new
  HelperBase derived class, (and a handler for incoming messages.) Outgoing
  messages can be sent for anywhere you like (normally other handlers.)
  """
  def __init__(self):
    # Maps connection objects to handler methods.
    self._incoming_connections = {}

  def setup_helper(self, helper, handler):
    self._incoming_connections[helper.connection] = handler
    helper.start()

  def run_forever(self):
    while True:
      rread = self._incoming_connections.keys()
      print "Blocking on: %s" % rread
      rready, _, _ = select.select(self._incoming_connections.keys(), [], [])
      print "Unblocked on: %s" % rready

      for c in rready:
        try:
          self._incoming_connections[c](c.recv())
        # pylint: disable=W0703
        except Exception:
          # If we get an exception in a handler, we log and continue.
          traceback.print_exc()
