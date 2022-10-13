#! /usr/bin/env python
#
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT

import argparse
import os
import sys


COPYRIGHT_AND_LICENSE_DISCLAIMER = "# Copyright © 2022 Intel Corporation\n#\n# SPDX-License-Identifier: MIT\n"

def file_has_disclaimer(filename, verbose=False):
  if verbose:
    print(f"Checking: {filename}")
  with open(filename) as fp:
    # NOTE: allow shebang+empty line before
    header = "".join(fp.readline() for _ in range(5))
  return COPYRIGHT_AND_LICENSE_DISCLAIMER in header


def check_all(directory, verbose=False):
  missing = []
  for dirpath, dirnames, filenames in os.walk(directory):
    for filename in filenames:
      absolute_filename = os.path.join(dirpath, filename)
      if is_file_relevant(absolute_filename):
        if not file_has_disclaimer(absolute_filename, verbose=verbose):
          missing.append(absolute_filename)
  return missing


def is_file_relevant(filename):
  return filename.endswith((".py", "Dockerfile")) and os.stat(filename).st_size > 0

def fix_in_place(filename, verbose):
  if verbose:
    print(f"Fixing {filename}")
  with open(filename, "r+") as fp:
    maybe_shebang = fp.readline()
    remaining = fp.read()

    fp.seek(0)

    if maybe_shebang.startswith("#!"):
      fp.write(maybe_shebang + "#\n" + COPYRIGHT_AND_LICENSE_DISCLAIMER + remaining)
    else:
      fp.write(COPYRIGHT_AND_LICENSE_DISCLAIMER + maybe_shebang + remaining)

def fix_all(filenames, verbose=False):
  failed_to_fix = []
  for filename in filenames:
    try:
      fix_in_place(filename, verbose=verbose)
    except Exception as e:
      print(f"failed to fix {filename}: {e}")
      failed_to_fix.append(filename)
    if not file_has_disclaimer(filename):
      print(f"fix did not work for {filename}")
      failed_to_fix.append(filename)
  return failed_to_fix


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("directory")
  parser.add_argument("--fix-in-place", "-f", action="store_true")
  parser.add_argument("--verbose", "-v", action="store_true")

  args = parser.parse_args()
  missing = check_all(args.directory, verbose=args.verbose)
  if args.fix_in_place:
    missing = fix_all(missing)
  if missing:
    print("The following files failed the copyright + license check:\n\t" + "\n\t".join(f for f in missing))
    sys.exit(1)
