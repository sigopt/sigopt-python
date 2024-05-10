#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: MIT
set -e
set -o pipefail

exec vulture --exclude="build,venv" --ignore-decorators="@click.*,@sigopt_cli.*,@public,@pytest.*" --ignore-names="side_effect" "$@"
