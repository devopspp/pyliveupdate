import socket
import threading
import sys
from io import StringIO
from werkzeug import local

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

class IORedirecter(object):
    def __init__(self):
        # Save all of the objects for use later.
        self.orig___stdout__ = sys.__stdout__
        self.orig___stderr__ = sys.__stderr__
        self.orig_stdout = sys.stdout
        self.orig_stderr = sys.stderr
        self.thread_proxies = {}

    def redirect(self):
        """
        Enables the redirect for the current thread's output to a single StringIO
        object and returns the object.

        :return: The StringIO object.
        :rtype: ``StringIO``
        """
        # Get the current thread's identity.
        ident = threading.currentThread().ident

        # Enable the redirect and return the StringIO object.
        self.thread_proxies[ident] = StringIO()
        return self.thread_proxies[ident]


    def stop_redirect(self):
        """
        Enables the redirect for the current thread's output to a single cStringIO
        object and returns the object.

        :return: The final string value.
        :rtype: ``str``
        """
        # Get the current thread's identity.
        ident = threading.currentThread().ident

        # Only act on proxied threads.
        if ident not in self.thread_proxies:
            return

        # Read the value, close/remove the buffer, and return the value.
        retval = self.thread_proxies[ident].getvalue()
        self.thread_proxies[ident].close()
        del self.thread_proxies[ident]
        return retval


    def _get_stream(self, original):
        """
        Returns the inner function for use in the LocalProxy object.

        :param original: The stream to be returned if thread is not proxied.
        :type original: ``file``
        :return: The inner function for use in the LocalProxy object.
        :rtype: ``function``
        """
        def proxy():
            """
            Returns the original stream if the current thread is not proxied,
            otherwise we return the proxied item.

            :return: The stream object for the current thread.
            :rtype: ``file``
            """
            # Get the current thread's identity.
            ident = threading.currentThread().ident

            # Return the proxy, otherwise return the original.
            return self.thread_proxies.get(ident, original)

        # Return the inner function.
        return proxy


    def enable_proxy(self):
        """
        Overwrites __stdout__, __stderr__, stdout, and stderr with the proxied
        objects.
        """
        sys.__stdout__ = local.LocalProxy(self._get_stream(sys.__stdout__))
        sys.__stderr__ = local.LocalProxy(self._get_stream(sys.__stderr__))
        sys.stdout = local.LocalProxy(self._get_stream(sys.stdout))
        sys.stderr = local.LocalProxy(self._get_stream(sys.stderr))


    def disable_proxy(self):
        """
        Overwrites __stdout__, __stderr__, stdout, and stderr with the original
        objects.
        """
        sys.__stdout__ = self.orig___stdout__
        sys.__stderr__ = self.orig___stderr__
        sys.stdout = self.orig_stdout
        sys.stderr = self.orig_stderr
        self.thread_proxies = {}