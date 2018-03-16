import os
import sys
import platform
import ms.version

PYTHON_VERSION = platform.python_version()
SYSTEM = platform.system()


def get_python_version():
    global SYSTEM, PYTHON_VERSION
    if SYSTEM == 'Windows':
        return 'py_win'
    elif PYTHON_VERSION.startswith('3') or PYTHON_VERSION.endswith('-64'):
        return 'py3'
    else:
        return 'py2'


def get_version(package):
    python_versions = {}
    if package == 'reportlab':
        python_versions = {
            'py_win': ('reportlab', '3.4.0-ms1'),
            'py3': ('reportlab', '3.4.0'),
            'py2': ('reportlab', '2.7'),
        }

    if package == 'Pillow':
        python_versions = {
            'py_win': ('Pillow', '3.4.1'),
            'py3': ('Pillow', '3.4.1'),
            'py2': ('pil', '1.1.7'),
        }

    if len(python_versions) > 0:
        return python_versions[get_python_version()]
    else:
        raise KeyError('No such package: {}'.format(package))

requirements = (
    ('pytest', '2.8.7'),
    ('py', '1.4.31'),
    ('psutil', '5.2.2'),
    ('six', '1.10.0'),
    ('future', '0.15.2'),
    ('setuptools', '23.0.0'),
    ('schema', '0.6.6'),
    ('pytz', '2016.6.1'),
    ('lxml', '3.8.0'),
    ('dateutil', '2.6.0'),
    get_version('reportlab'),
    ('marshmallow', '3.0.0b2'),
    ('schema', '0.6.6'),
    ('mock', '1.0.1-py27'),
    ('termcolor', '1.1.0'),
    ('colorama', '0.3.7'),
    ('enum34', '1.1.6'),
    ('pyzmq', '16.0.2-ms3'),
    ('terminaltables', '3.1.0'),
    ('numpy', '1.13.3'),
    ('pyparsing', '2.0.3'),
    ('cycler', '0.10.0'),
    ('functools32', '3.2.3-1'),
    ('matplotlib', '2.0.2'),
    get_version('Pillow'),
)

# NOTE: these are not OSS dependencies
requirements += (
    ('sklearn', '0.19b2'),
    ('scipy', '1.0.0'),
    ('ms.fix', '2018.03.15-1'),
)

for package, version in requirements:
    try:
        ms.version.addpkg(package, version)
    except:
        ms.version.addpkg(package, version, location='dev')

import pyfixmsg
os.environ['PYFIXMSG_PATH'] = os.path.join(os.path.dirname(pyfixmsg.__file__), '..')
os.environ['FIX_SPEC_FILE'] = os.path.join(os.path.dirname(pyfixmsg.__file__), '..', 'spec', 'FIX42.xml')

src_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')

sys.path.append(src_dir)
