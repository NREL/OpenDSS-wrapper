#!/usr/bin/env python
import io
import os
import re
from setuptools import find_packages

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

requirements = [
    'numpy',
    'pandas',
    'OpenDSSDirect.py[extras]',
]


# Read the version from the __init__.py file without importing it
def read(*names, **kwargs):
    with io.open(
            os.path.join(os.path.dirname(__file__), *names),
            encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(name='OpenDSS-wrapper',
      version=find_version('opendss_wrapper', '__init__.py'),
      description='Distribution system simulation python wrapper to connect OpenDSSDirect.py with a co-simulation framework',
      author='Michael Blonsky',
      author_email='Michael.Blonsky@nrel.gov',
      url='https://github.com/NREL/OpenDSS-wrapper',
      packages=find_packages(),
      install_requires=requirements,
      package_data={'opendss_wrapper': []},
      )
