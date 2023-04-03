#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT

import argparse
import os
import sys


COPYRIGHT = "Copyright © 2022 Intel Corporation"
LICENSE = "SPDX-License-Identifier: MIT"


class Filetype:
  python = ".py"
  dockerfile = "Dockerfile"


FILETYPES = (
  Filetype.python,
  Filetype.dockerfile,
)

COMMENT_BLOCKS = {
  Filetype.python: ("", ""),
  Filetype.dockerfile: ("", ""),
}

COMMENT_LINES = {
  Filetype.python: "#",
  Filetype.dockerfile: "#",
}


def guess_filetype(filename):
  for filetype in FILETYPES:
    if filename.endswith(filetype):
      return filetype
    # Filenames like "Dockerfile.api" are allowed
    if os.path.basename(filename).startswith(Filetype.dockerfile):
      return Filetype.dockerfile
  return None


def generate_disclaimer(filetype):
  opener, closer = COMMENT_BLOCKS[filetype]
  separator = COMMENT_LINES[filetype]
  return f"{opener}{separator} {COPYRIGHT}\n{separator}\n{separator} {LICENSE}\n{closer}"


def file_has_disclaimer(filename, filetype, verbose=False):
  if verbose:
    print(f"Checking: {filename}")
  with open(filename) as fp:
    # NOTE: allow shebang before
    header = "".join(fp.readline() for _ in range(5))
  return generate_disclaimer(filetype) in header


def check_all(files, verbose=False):
  missing = []
  for filename in files:
    filetype = guess_filetype(filename)
    if filetype and os.stat(filename).st_size > 0:
      if not file_has_disclaimer(filename, filetype, verbose=verbose):
        missing.append(filename)
  return missing


def fix_in_place(filename, filetype, verbose):
  if verbose:
    print(f"Fixing {filename}")

  disclaimer = generate_disclaimer(filetype)
  with open(filename, "r+") as fp:
    maybe_shebang = fp.readline()
    remaining = fp.read()

    fp.seek(0)

    if maybe_shebang.startswith("#!"):
      fp.write(maybe_shebang + disclaimer + remaining)
    else:
      fp.write(disclaimer + maybe_shebang + remaining)


def fix_all(filenames, verbose=False):
  failed_to_fix = []
  for filename in filenames:
    filetype = guess_filetype(filename)
    try:
      fix_in_place(filename, filetype, verbose=verbose)
    except Exception as e:
      print(f"failed to fix {filename}: {e}")
      failed_to_fix.append(filename)
    if not file_has_disclaimer(filename, filetype):
      print(f"fix did not work for {filename}")
      failed_to_fix.append(filename)
  return failed_to_fix


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("files", nargs="+")
  parser.add_argument("--fix-in-place", "-f", action="store_true")
  parser.add_argument("--verbose", "-v", action="store_true")

  args = parser.parse_args()
  missing = check_all(args.files, verbose=args.verbose)
  if args.fix_in_place:
    missing = fix_all(missing, verbose=args.verbose)
  if missing:
    print("\nThe following files failed the copyright + license check:\n\t" + "\n\t".join(f for f in missing))
    sys.exit(1)
  else:
    if args.verbose:
      print("\nAll files have disclaimer")
