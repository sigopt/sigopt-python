# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click


commands_argument = click.argument('commands', nargs=-1, type=click.UNPROCESSED)
