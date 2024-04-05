# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import os
import sys
import warnings

from setuptools import find_packages, setup


if sys.version_info[0] == 3 and sys.version_info[1] < 7:
  warnings.warn(
    (
      "Python versions lower than 3.7 are no longer supported. Please upgrade to"
      " Python 3.7 or newer or use an older version of the sigopt-python client."
    ),
    DeprecationWarning,
  )

# NOTE: We can't `import sigopt.version` directly, because that
# will cause us to execute `sigopt/__init__.py`, which may transitively import
# packages that may not have been installed yet. So jump straight to sigopt/version.py
# and execute that directly, which should be simple enough that it doesn't import anything
# Learned from https://github.com/stripe/stripe-python (MIT licensed)
version_contents = {}
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "sigopt", "version.py"), encoding="utf-8") as f:
  exec(f.read(), version_contents)  # pylint: disable=exec-used
VERSION = version_contents["VERSION"]

with open(os.path.join(here, "requirements.txt")) as requirements_fp:
  install_requires = requirements_fp.read().split("\n")
with open(os.path.join(here, "requirements-dev.txt")) as requirements_dev_fp:
  dev_install_requires = requirements_dev_fp.read().split("\n")

orchestrate_install_requires = [
  "Pint>=0.16.0,<0.17.0",
  "boto3>=1.16.34,<2.0.0",
  "certifi>=2022.12.7",
  "docker>=4.4.0,<5.0.0",
  "kubernetes>=12.0.1,<13.0.0",
  "pyOpenSSL>=20.0.0",
]
xgboost_install_requires = ["xgboost>=1.3.1", "numpy>=1.15.0"]
hyperopt_install_requires = ["hyperopt>=0.2.7"]
lite_install_requires = ["sigoptlite>=0.1.1"]

if sys.version_info[0] == 3 and sys.version_info[1] < 12:
  pytest_requires = ["pytest==7.2.1"]
else:
  pytest_requires = ["pytest>=7.2.1"]

setup(
  name="sigopt",
  version=VERSION,
  description="SigOpt Python API Client",
  author="SigOpt",
  author_email="support@sigopt.com",
  url="https://sigopt.com/",
  packages=find_packages(exclude=["tests*"]),
  package_data={
    "": ["*.ms", "*.txt", "*.yml", "*.yaml"],
  },
  install_requires=install_requires,
  extras_require={
    "dev": dev_install_requires
    + pytest_requires
    + orchestrate_install_requires
    + xgboost_install_requires
    + hyperopt_install_requires
    + lite_install_requires,
    "hyperopt": hyperopt_install_requires,
    "orchestrate": orchestrate_install_requires,
    "xgboost": xgboost_install_requires,
    "lite": lite_install_requires,
    "pytest": pytest_requires,
  },
  entry_points={
    "console_scripts": [
      "sigopt=sigopt.cli.__main__:sigopt_cli",
    ],
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
