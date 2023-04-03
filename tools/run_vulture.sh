#!/usr/bin/env bash

exec vulture --exclude="build,venv" --ignore-decorators="@click.*,@sigopt_cli.*,@pytest.*" "$@"
