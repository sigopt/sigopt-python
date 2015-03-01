from setuptools import setup

# keep this in sync with requirements.txt
install_requires=['requests>=2.0.1']

setup(
  name='sigopt-python',
  version='0.4.0',
  description='SigOpt Python API Client',
  author='SigOpt',
  author_email='support@sigopt.com',
  url='https://sigopt.com/',
  packages=['sigopt'],
  install_requires=install_requires,
  classifiers=[
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Software Development :: Libraries :: Python Modules",
  ]
)
