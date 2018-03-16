#!/ms/dist/python/PROJ/core/2.7.9-64/bin/python 
"""
from: doc/en
rm -rf ../../../build/html; ../../ms/scripts/bin/gen_docs.py -b html . ../../../build/html
"""

from __future__ import print_function
# MSVERSION PATCH
import importlib
import sys

try:
  import ms.version
except ImportError:

  sys.stderr.write("You must use python version 2.5.2 or later to run this script\n")
  sys.exit(1)

# Format :  (module, prefered_version, import_to_validate, alternate_versions)
dependencies = [
  ("setuptools", "14.0"),
  ("Whoosh", "2.7.0"),
  ("simplejson", "3.7.2"),
  ("sphinx_rtd_theme", "0.1.9"),
  ("snowballstemmer", "1.2.0"),
  ("alabaster", "0.7.3-ms1"),
  ("Babel", "1.3-ms1"),
  ("six", "1.7.3"),
  ("docutils", "0.12"),
  ("pytz", "2014.10"),
  ("markupsafe", "0.23-ms1", "markupsafe"),
  ("jinja2", "2.7.3"),
  ("nose", "1.3.6"),
  ("colorama", "0.3.2"),
  ("sqlalchemy", "0.9.7-ms1"),
  ("mock", "1.0.1"),
  ("pygments", "2.0.2-ms3"),
  ("imagesize", "0.7.0", "imagesize"),
  ("wsgiref", "0.1.2", "wsgiref")
]
if 'win' in sys.platform:
  sphinx_version = "1.3.1-ms1"
  sphinx_version_pkg = "1.3.1"
else:
  sphinx_version = "1.4b1"
  sphinx_version_pkg = "1.4b1"
ms.version.addpkg("Sphinx", sphinx_version)

for dep in dependencies:
  try:
    ms.version.addpkg(dep[0], dep[1])
  except ms.version.MSVersionError:
    ms.version.addpkg(dep[0], dep[1], "dev")
  if len(dep) > 2:
    try:
      print("Importing {}".format(dep[2]))
      importlib.import_module(dep[2])
    except ImportError:
      raise

import dependencies
from pkg_resources import load_entry_point

if __name__ == '__main__':
  sys.exit(
    load_entry_point('Sphinx=={}'.format(sphinx_version_pkg), 'console_scripts', 'sphinx-build')()
  )
