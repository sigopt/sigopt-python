import sys
import warnings

from setuptools import setup
from sigopt.version import VERSION

if sys.version_info < (2, 7):
  warnings.warn(
    'Python 2.6 is no longer supported.'
    ' Please upgrade to Python 2.7 or use version 2 of the sigopt-python client.',
    DeprecationWarning
  )

# keep this in sync with requirements.txt
install_requires = ['requests>=2.11.1']

setup(
  name='sigopt',
  version=VERSION,
  description='SigOpt Python API Client',
  author='SigOpt',
  author_email='support@sigopt.com',
  url='https://sigopt.com/',
  packages=['sigopt', 'sigopt.examples', 'sigopt.vendored'],
  install_requires=install_requires,
  extras_require={
    'dev': 'numpy>=1.11.3',
  },
  classifiers=[
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Software Development :: Libraries :: Python Modules",
  ],
)
