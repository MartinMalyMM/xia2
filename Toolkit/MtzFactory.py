#!/usr/bin/env cctbx.python
# MtzFactory.py
# 
#   Copyright (C) 2010 Diamond Light Source, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is 
#   included in the root directory of this package.
# 
# A toolkit component to read MTZ format reflection filesm, wrapping the
# functionality in iotbx. This will return a data structure to represent
# merged and unmerged MTZ files.

import sys
import math
import os
import time

from iotbx import mtz

class mtz_dataset:
    '''A class to represent the MTZ dataset in the hierarchy. This will
    be instantiated in the mtz_crystal class below, and contain:

     - a list of columns

    Maybe more things will be added.'''

    def __init__(self, iotbx_dataset):
        self._name = iotbx_dataset.name()
        self._columns = iotbx_dataset.columns()

        self._column_table = { }
        for column in self._columns:
            self._column_table[column.label()] = column
        
        return

    def get_column_names(self):
        return [column.label() for column in self._columns]

    def get_column_values(self, column_label, nan_value = 0.0):
        return self._column_table[column_label].extract_values(
            not_a_number_substitute = nan_value)

class mtz_crystal:
    '''A class to represent the MTZ crystal in the hierarchy. This will
    be instantiated by the factories below.'''

    def __init__(self, iotbx_crystal):
        self._name = iotbx_crystal.name()
        self._datasets = iotbx_crystal.datasets()
        self._unit_cell = iotbx_crystal.unit_cell()

        self._dataset_table = { }
        for dataset in self._datasets:
            self._dataset_table[dataset.name()] = mtz_dataset(dataset)

        return

    def get_datasets(self):
        return [dataset.name() for dataset in self._datasets]

    def get_dataset(self, dataset_name):
        return self._dataset_table[dataset_name]

    def get_unit_cell(self):
        return tuple(self._unit_cell.parameters())

class mtz_file:
    '''A class to represent the full MTZ file in the hierarchy - this
    will have a list of one or more crystals contained within it each
    with its own unit cell and datasets.'''

    # FIXME need to keep in mind MTZ batch headers - can I access these?

    def __init__(self, hklin):
        mtz_obj = mtz.object(hklin)

        self._miller_indices = mtz_obj.extract_miller_indices()
        self._resolution_range = mtz_obj.max_min_resolution()
        self._space_group = mtz_obj.space_group()
        self._crystals = mtz_obj.crystals()

        self._crystal_table = { }
        for crystal in self._crystals:
            self._crystal_table[crystal.name()] = mtz_crystal(crystal)

        return

    def get_crystal_names(self):
        return [crystal.name() for crystal in self._crystals]

    def get_crystal(self, crystal_name):
        return self._crystal_table[crystal_name]

    def get_space_group(self):
        return self._space_group

def mtz_dump(hklin):
    '''An implementation of mtzdump using the above classes.'''

    mtz = mtz_file(hklin)

    print 'Reading file: %s' % hklin
    print 'Spacegroup: %s' % mtz.get_space_group().type(
         ).universal_hermann_mauguin_symbol()

    for xname in mtz.get_crystal_names():
        crystal = mtz.get_crystal(xname)
        print 'Crystal: %s' % xname
        print 'Cell: %.3f %.3f %.3f %.3f %.3f %.3f' % crystal.get_unit_cell()

        for dname in crystal.get_datasets():
            dataset = crystal.get_dataset(dname)
            print 'Dataset: %s' % dname
            print 'Columns (with min / max)'
            for column in dataset.get_column_names():
                values = dataset.get_column_values(column)
                print '%20s %.4e %.4e' % (column, min(values), max(values))

if __name__ == '__main__':
    import sys

    mtz_dump(sys.argv[1])

    
        
