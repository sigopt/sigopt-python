from codecs import open
import os
import sys
import warnings

from setuptools import setup

if sys.version_info < (2, 7):
  warnings.warn(
    'Python 2.6 is no longer supported.'
    ' Please upgrade to Python 2.7 or use version 2 of the sigopt-python client.',
    DeprecationWarning
  )

# keep this in sync with requirements.txt
install_requires = ['requests>=2.11.1']

# NOTE(patrick): We can't `import sigopt.version` directly, because that
# will cause us to execute `sigopt/__init__.py`, which may transitively import
# packages that may not have been installed yet. So jump straight to sigopt/version.py
# and execute that directly, which should be simple enough that it doesn't import anything
# Learned from https://github.com/stripe/stripe-python (MIT licensed)
version_contents = {}
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'sigopt', 'version.py'), encoding='utf-8') as f:
  exec(f.read(), version_contents)
VERSION = version_contents['VERSION']

setup(
  name='sigopt',
  version=VERSION,
  description='SigOpt Python API Client',
  author='SigOpt',
  author_email='support@sigopt.com',
  url='https://sigopt.com/',
  packages=['sigopt', 'sigopt.examples', 'sigopt.vendored'],
  install_requires=install_requires,
  classifiers=[
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Software Development :: Libraries :: Python Modules",
  ],
)
