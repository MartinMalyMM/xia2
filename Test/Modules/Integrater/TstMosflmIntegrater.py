import os
import sys
if not os.environ.has_key('XIA2CORE_ROOT'):
  raise RuntimeError, 'XIA2CORE_ROOT not defined'

if not os.environ.has_key('XIA2_ROOT'):
  raise RuntimeError, 'XIA2_ROOT not defined'

if not os.path.join(os.environ['XIA2CORE_ROOT'],
                    'Python') in sys.path:
  sys.path.append(os.path.join(os.environ['XIA2CORE_ROOT'],
                               'Python'))

if not os.environ['XIA2_ROOT'] in sys.path:
  sys.path.append(os.environ['XIA2_ROOT'])

import libtbx.load_env
from libtbx import easy_run
from libtbx.test_utils import approx_equal, open_tmp_directory, show_diff

try:
  dials_regression = libtbx.env.dist_path('dials_regression')
  have_dials_regression = True
except KeyError, e:
  have_dials_regression = False


def exercise_mosflm_integrater():
  if not have_dials_regression:
    print "Skipping exercise_mosflm_integrater(): dials_regression not configured"
    return

  xia2_demo_data = os.path.join(dials_regression, "xia2_demo_data")
  template = os.path.join(xia2_demo_data, "insulin_1_%03i.img")

  cwd = os.path.abspath(os.curdir)
  tmp_dir = os.path.abspath(open_tmp_directory())
  os.chdir(tmp_dir)


  from Modules.Indexer.MosflmIndexer import MosflmIndexer
  from Modules.Integrater.MosflmIntegrater import MosflmIntegrater
  indexer = MosflmIndexer()
  indexer.set_working_directory(tmp_dir)
  indexer.setup_from_image(template %1)

  from Schema.XCrystal import XCrystal
  from Schema.XWavelength import XWavelength
  from Schema.XSweep import XSweep
  cryst = XCrystal("CRYST1", None)
  wav = XWavelength("WAVE1", cryst, indexer.get_wavelength())
  directory, image = os.path.split(template %1)
  sweep = XSweep('SWEEP1', wav, directory=directory, image=image)
  indexer.set_indexer_sweep(sweep)

  integrater = MosflmIntegrater()
  integrater.set_working_directory(tmp_dir)
  integrater.setup_from_image(template %1)
  integrater.set_integrater_indexer(indexer)
  integrater.set_integrater_sweep(sweep)
  integrater.integrate()

  integrater_intensities = integrater.get_integrater_intensities()
  assert os.path.exists(integrater_intensities)
  from iotbx.reflection_file_reader import any_reflection_file
  reader = any_reflection_file(integrater_intensities)
  assert reader.file_type() == "ccp4_mtz"
  mtz_object = reader.file_content()
  assert mtz_object.n_reflections() == 81057
  assert mtz_object.column_labels() == [
    'H', 'K', 'L', 'M_ISYM', 'BATCH', 'I', 'SIGI', 'IPR', 'SIGIPR',
    'FRACTIONCALC', 'XDET', 'YDET', 'ROT', 'WIDTH', 'LP', 'MPART', 'FLAG',
    'BGPKRATIOS']

  assert integrater.get_integrater_wedge() == (1, 45)
  assert approx_equal(integrater.get_integrater_cell(),
                      (78.014, 78.014, 78.014, 90.0, 90.0, 90.0), eps=1e-3)

def run():
  exercise_mosflm_integrater()
  print "OK"


if __name__ == '__main__':
  run()
