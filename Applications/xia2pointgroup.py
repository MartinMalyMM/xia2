#!/usr/bin/env python
# xia2pointgroup.py
#   Copyright (C) 2006 CCLRC, Graeme Winter
#
#   This code is distributed under the terms and conditions of the
#   CCP4 Program Suite Licence Agreement as a CCP4 Library.
#   A copy of the CCP4 licence can be obtained by writing to the
#   CCP4 Secretary, Daresbury Laboratory, Warrington WA4 4AD, UK.
#
# 10th August 2006
# 
# A small program to integrate in P1 a wedge of images and display
# the output of pointless run on these images.
#
# FIXME this is probably not using the proper interfaces...
# 

import sys
import os

if not os.environ.has_key('DPA_ROOT'):
    raise RuntimeError, 'DPA_ROOT not defined'
if not os.environ.has_key('XIA2CORE_ROOT'):
    raise RuntimeError, 'XIA2CORE_ROOT not defined'

sys.path.append(os.path.join(os.environ['DPA_ROOT']))

from Handlers.CommandLine import CommandLine
from Schema.Sweep import SweepFactory

# program wrappers we will use
from Wrappers.Labelit.LabelitScreen import LabelitScreen
from Wrappers.CCP4.Mosflm import Mosflm
from Wrappers.CCP4.Pointless import Pointless

def xia2pointgroup():
    '''Do it!'''

    l = LabelitScreen()

    l.setup_from_image(CommandLine.getImage())

    phi_width = l.getHeader_item('phi_width')
    images = l.getMatching_images()

    l.add_indexer_image_wedge(images[0])
    if int(90 / phi_width) in images:
        l.add_indexer_image_wedge(int(90/ phi_width))
    else:
        l.add_indexer_image_wedge(images[-1])

    # integrate in P1
    l.set_indexer_input_lattice('aP')

    for width in [5.0, 10.0, 15.0, 30.0]:
        if len(images) * phi_width >= width:
            m = Mosflm()
            m.setup_from_image(CommandLine.getImage())
            m.integrate_set_indexer(l)
            m.integrate_set_wedge(images[0],
                                  images[0] + int(width / phi_width))
            
            p = Pointless()
            hklout = m.integrate(fast = True)
            p.setHklin(hklout)
            p.decide_pointgroup()

            print '%f %s %f' % (width, p.getPointgroup(), p.getConfidence())

if __name__ == '__main__':
    xia2pointgroup()

            
            
