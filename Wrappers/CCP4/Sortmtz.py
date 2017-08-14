#!/usr/bin/env python
# Sortmtz.py
#   Copyright (C) 2006 CCLRC, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is
#   included in the root directory of this package.
#
# 5th June 2006
#
# A wrapper for the CCP4 program sortmtz.

from __future__ import absolute_import, division

import os

from xia2.Driver.DriverFactory import DriverFactory
from xia2.Decorators.DecoratorFactory import DecoratorFactory
from xia2.Handlers.Streams import Chatter

def Sortmtz(DriverType = None):
  '''A factory for SortmtzWrapper classes.'''

  DriverInstance = DriverFactory.Driver(DriverType)
  CCP4DriverInstance = DecoratorFactory.Decorate(DriverInstance, 'ccp4')

  class SortmtzWrapper(CCP4DriverInstance.__class__):
    '''A wrapper for Sortmtz, using the CCP4-ified Driver.'''

    def __init__(self):
      # generic things
      CCP4DriverInstance.__class__.__init__(self)

      self.set_executable(os.path.join(
          os.environ.get('CBIN', ''), 'sortmtz'))

      self._sort_order = 'H K L M/ISYM BATCH'

      self._hklin_files = []

      return

    def add_hklin(self, hklin):
      '''Add a reflection file to the list to be sorted together.'''
      self._hklin_files.append(hklin)
      return

    def check_sortmtz_errors(self):
      '''Check the output for "standard" errors.'''

      lwbat_warning = ''

      for l in self.get_all_output():

        if 'From ccp4_lwbat: warning:' in l:
          lwbat_warning = l.split('warning:')[1].strip()

        if 'error in ccp4_lwbat' in l:
          raise RuntimeError, lwbat_warning

        if 'Sorting failed' in l:
          raise RuntimeError, 'sorting failed'

        if 'Inconsistent operator orders in input file' in l:
          raise RuntimeError, 'different sort orders'

    def sort(self, vrset = None):
      '''Actually sort the reflections.'''

      # if we have not specified > 1 hklin file via the add method,
      # check that the set_hklin method has been used. If exactly one
      # set this as HKLIN on command line as a workaround for a bug
      # in sortmtz with big reflection files giving SEGV

      if len(self._hklin_files) == 1:
        self.set_hklin(self._hklin_files[0])
        self._hklin_files = []

      if not self._hklin_files:
        self.check_hklin()

      self.check_hklout()

      if self._hklin_files:
        task = ''
        for hklin in self._hklin_files:
          task += ' %s' % hklin
        self.set_task('Sorting reflections%s => %s' % \
                     (task,
                      os.path.split(self.get_hklout())[-1]))
      else:
        self.set_task('Sorting reflections %s => %s' % \
                     (os.path.split(self.get_hklin())[-1],
                      os.path.split(self.get_hklout())[-1]))

      self.start()

      # allow for the fact that large negative reflections may
      # result from XDS output...

      if vrset:
        self.input('VRSET_MAGIC %f' % vrset)

      self.input(self._sort_order)

      # multiple mtz files get passed in on the command line...

      if self._hklin_files:
        for m in self._hklin_files:
          self.input('"%s"' % m)

      self.close_wait()

      try:

        # general errors - SEGV and the like
        self.check_for_errors()

        # ccp4 specific errors
        self.check_ccp4_errors()
        if 'Error' in self.get_ccp4_status():
          raise RuntimeError, '[SORTMTZ] %s' % status

        # sortmtz specific errors
        self.check_sortmtz_errors()

      except RuntimeError, e:
        # something went wrong; remove the output file
        try:
          os.remove(self.get_hklout())
        except:
          pass
        raise e

      return self.get_ccp4_status()

  return SortmtzWrapper()

