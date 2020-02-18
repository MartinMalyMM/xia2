# "Standard" output streams for the output of xia2 - these will allow
# filtering of the output to files, the standard output, a GUI, none of
# the above, all of the above.
#
# The idea of this is to separate the "administrative", "status" and
# "scientific" output of the program.

from __future__ import absolute_import, division, print_function

import itertools
import logging
import os
import platform
import sys
from datetime import date

import libtbx.load_env

if not hasattr(logging, "NOTICE"):
    # Create a NOTICE log level and associated command
    logging.NOTICE = 25

    def _notice(self, *args, **kwargs):
        return self.log(logging.NOTICE, *args, **kwargs)

    logging.getLoggerClass().notice = _notice


def _logger_file(loggername, level=logging.INFO):
    "Returns a file-like object that writes to a logger"
    log_function = logging.getLogger(loggername).log

    class _(object):
        @staticmethod
        def flush():
            pass

        @staticmethod
        def write(logobject):
            if logobject.endswith("\n"):
                # the Stream.write() function adds a trailing newline.
                # remove that again
                logobject = logobject[:-1]
            log_function(level, logobject)

    return _()


def banner(comment, size=60):
    if not comment:
        return "-" * size

    l = len(comment)
    m = (size - (l + 2)) // 2
    n = size - (l + 2 + m)
    return "%s %s %s" % ("-" * m, comment, "-" * n)


class _Stream(object):
    """A class to represent an output stream. This will be used as a number
    of static instances - Chatter in particular."""

    def __init__(self, streamname, file=None):
        """Create a new stream."""

        # FIXME would rather this goes to a file...
        # unless this is impossible

        self._file = file
        self._filter = None
        self._prefix = None

    def filter(self, filter):
        self._filter = filter

    def write(self, record, strip=True):
        if self._filter:
            for replace in self._filter:
                record = record.replace(replace, self._filter[replace])

        for r in record.split("\n"):
            if self._prefix:
                result = self._file.write(
                    u"[%s]  %s\n" % (self._prefix, r.strip() if strip else r)
                )
            else:
                result = self._file.write(u"%s\n" % (r.strip() if strip else r))

            self._file.flush()

        return result


cl = libtbx.env.dispatcher_name
if cl:
    if "xia2" not in cl or "python" in cl or cl == "xia2.new":
        cl = "xia2"
else:
    cl = "xia2"

if cl.endswith(".bat"):
    # windows adds .bat extension to dispatcher
    cl = cl[:-4]

Chatter = _Stream("%s" % cl, file=_logger_file("xia2.stream.chatter"))
today = date.today()
sanitize = (today.day == 1 and today.month == 4) or "XIA2_APRIL" in os.environ


def setup_logging(logfile=None, debugfile=None, verbose=False):
    """
    Initialise logging for xia2

    :param logfile: Filename for info/info+debug log output.
    :type logfile: str
    :param debugfile: Filename for debug log output.
    :type debugfile: str
    :param verbose: Enable debug output for logfile and console.
    :type verbose: bool
    """
    if verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    if sys.stdout.isatty() and not os.getenv("NO_COLOR"):
        console = ColorStreamHandler(sys.stdout)
    else:
        console = logging.StreamHandler(sys.stdout)
    console.setLevel(loglevel)

    xia2_logger = logging.getLogger("xia2")
    xia2_logger.addHandler(console)
    xia2_logger.setLevel(loglevel)

    other_loggers = [logging.getLogger(package) for package in ("dials", "dxtbx")]

    if logfile:
        fh = logging.FileHandler(filename=logfile, mode="w")
        fh.setLevel(loglevel)
        xia2_logger.addHandler(fh)
        for logger in other_loggers:
            logger.addHandler(fh)
            logger.setLevel(loglevel)

    if debugfile:
        fh = logging.FileHandler(filename=debugfile, mode="w")
        fh.setLevel(logging.DEBUG)
        for logger in [xia2_logger] + other_loggers:
            logger.addHandler(fh)
            logger.setLevel(logging.DEBUG)


if __name__ == "__main__":
    setup_logging(logfile="logfile", debugfile="debugfile")
    Chatter.write("nothing much, really")
    logging.getLogger("xia2.Handlers.Streams").debug("this is a debug-level message")


# -------------------------------------------------------------------------------
# colored stream handler for python logging framework based on:
# http://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output/1336640#1336640

# Copyright (c) 2014 Markus Pointner
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


class _AnsiColorStreamHandler(logging.StreamHandler):
    DEFAULT = "\x1b[0m"
    RED = "\x1b[31m"
    GREEN = "\x1b[32m"
    YELLOW = "\x1b[33m"
    BLUE = "\x1b[34m"
    PURPLE = "\x1b[35m"
    CYAN = "\x1b[36m"
    BOLD = "\x1b[1m"
    ANY = (GREEN, CYAN, BLUE, PURPLE, RED, YELLOW)

    CRITICAL = RED + BOLD
    ERROR = RED + BOLD
    WARNING = YELLOW + BOLD
    NOTICE = GREEN + BOLD
    INFO = ""
    DEBUG = BLUE

    encoding = 0

    @classmethod
    def _get_color(cls, level):
        if level >= logging.CRITICAL:
            return cls.CRITICAL
        elif level >= logging.ERROR:
            return cls.ERROR
        elif level >= logging.WARNING:
            return cls.WARNING
        elif level >= logging.NOTICE:
            return cls.NOTICE
        elif level >= logging.INFO:
            return cls.INFO
        elif level >= logging.DEBUG:
            return cls.DEBUG
        else:
            return ""

    def format(self, record):
        text = logging.StreamHandler.format(self, record)
        if sanitize:
            # ensure unicode is handled correctly
            if record.levelno >= logging.INFO:
                self.encoding = (self.encoding + 1) % len(self.ANY)
            clean_list = self.ANY[-self.encoding :] + self.ANY[: -self.encoding]
            tumblencode = getattr(itertools, "cycle")(clean_list)
            return (
                "".join(c + cc for c, cc in itertools.izip(tumblencode, text))
                + self.DEFAULT
            )
        colour = self._get_color(record.levelno)
        if colour:
            return colour + text + self.DEFAULT
        else:
            return text


class _WinColorStreamHandler(logging.StreamHandler):
    # wincon.h
    FOREGROUND_BLACK = 0x0000
    FOREGROUND_BLUE = 0x0001
    FOREGROUND_GREEN = 0x0002
    FOREGROUND_CYAN = 0x0003
    FOREGROUND_RED = 0x0004
    FOREGROUND_MAGENTA = 0x0005
    FOREGROUND_YELLOW = 0x0006
    FOREGROUND_GREY = 0x0007
    FOREGROUND_INTENSITY = 0x0008  # foreground color is intensified.
    FOREGROUND_WHITE = FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_RED

    BACKGROUND_BLACK = 0x0000
    BACKGROUND_BLUE = 0x0010
    BACKGROUND_GREEN = 0x0020
    BACKGROUND_CYAN = 0x0030
    BACKGROUND_RED = 0x0040
    BACKGROUND_MAGENTA = 0x0050
    BACKGROUND_YELLOW = 0x0060
    BACKGROUND_GREY = 0x0070
    BACKGROUND_INTENSITY = 0x0080  # background color is intensified.

    DEFAULT = FOREGROUND_WHITE
    CRITICAL = (
        BACKGROUND_YELLOW | FOREGROUND_RED | FOREGROUND_INTENSITY | BACKGROUND_INTENSITY
    )
    ERROR = FOREGROUND_RED | FOREGROUND_INTENSITY
    WARNING = FOREGROUND_YELLOW | FOREGROUND_INTENSITY
    NOTICE = FOREGROUND_GREEN | FOREGROUND_INTENSITY
    INFO = FOREGROUND_WHITE
    DEBUG = FOREGROUND_CYAN

    @classmethod
    def _get_color(cls, level):
        if level >= logging.CRITICAL:
            return cls.CRITICAL
        elif level >= logging.ERROR:
            return cls.ERROR
        elif level >= logging.WARNING:
            return cls.WARNING
        elif level >= logging.NOTICE:
            return cls.NOTICE
        elif level >= logging.INFO:
            return cls.INFO
        elif level >= logging.DEBUG:
            return cls.DEBUG
        else:
            return cls.DEFAULT

    def _set_color(self, code):
        import ctypes

        ctypes.windll.kernel32.SetConsoleTextAttribute(self._outhdl, code)

    def __init__(self, stream=None):
        logging.StreamHandler.__init__(self, stream)
        # get file handle for the stream
        import ctypes
        import ctypes.util

        # for some reason find_msvcrt() sometimes doesn't find msvcrt.dll on my system?
        crtname = ctypes.util.find_msvcrt()
        if not crtname:
            crtname = ctypes.util.find_library("msvcrt")
        crtlib = ctypes.cdll.LoadLibrary(crtname)
        self._outhdl = crtlib._get_osfhandle(self.stream.fileno())

    def emit(self, record):
        color = self._get_color(record.levelno)
        self._set_color(color)
        logging.StreamHandler.emit(self, record)
        self._set_color(self.FOREGROUND_WHITE)


# select ColorStreamHandler based on platform
if platform.system() == "Windows":
    ColorStreamHandler = _WinColorStreamHandler
else:
    ColorStreamHandler = _AnsiColorStreamHandler

# -------------------------------------------------------------------------------
