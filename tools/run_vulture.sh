#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: MIT

exec vulture --exclude="build,venv" --ignore-decorators="@click.*,@sigopt_cli.*,@pytest.*" "$@"
