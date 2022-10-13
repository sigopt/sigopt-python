# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
FROM python:3.9

USER root
RUN set -ex; apt-get -y update; apt-get -y install gcc
RUN set -ex; useradd sigopt; mkdir -p /sigopt
USER sigopt

COPY venv_requirements.txt /sigopt/venv_requirements.txt
RUN pip install --user -r /sigopt/venv_requirements.txt

COPY . /sigopt
WORKDIR /sigopt
