#!/usr/bin/env python
# Findspots.py
#
#   Copyright (C) 2013 Diamond Light Source, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is
#   included in the root directory of this package.
#
# Find spots for autoindexing - now separating this out into two steps; finding
# spots in index prepare and doing indexing in index proper.

def Findspots(DriverType = None):
    '''A factory for FindspotsWrapper(ipmosflm) classes.'''

    from Driver.DriverFactory import DriverFactory
    DriverInstance = DriverFactory.Driver(DriverType)

    class FindspotsWrapper(DriverInstance.__class__):

        def __init__(self):
            DriverInstance.__class__.__init__(self)

            from Handlers.Executables import Executables
            if Executables.get('ipmosflm'):
                self.set_executable(Executables.get('ipmosflm'))
            else:
                import os
                self.set_executable(os.path.join(
                    os.environ['CCP4'], 'bin', 'ipmosflm'))

            return

        def __call__(self, fp, images):
            from Handlers.Streams import Debug
            Debug.write('Running mosflm to find spots')

            self.start()
            self.input('template "%s"' % fp.get_template())
            self.input('directory "%s"' % fp.get_directory())
            self.input('beam %f %f' % fp.get_beam())
            self.input('distance %f' % fp.get_distance())
            self.input('wavelength %f' % fp.get_wavelength())
            self.input('findspots file spots.dat')
            for i in images:
                self.input('findspots find %d' % i)
            self.input('go')
            self.close_wait()

            # FIXME I should really gather some interesting information about
            # the spot finding in here...
            
            import os            
            return os.path.join(self.get_working_directory(), 'spots.dat')
        
    return FindspotsWrapper()
