FROM python:3.6.12-slim

RUN set -ex \
  ; apt-get update -yqq \
  ; apt-get install -yqq git \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

RUN pip install --no-cache-dir kubernetes==12.0.1 git+https://github.com/sigopt/sigopt-python.git@sj/main

COPY controller /usr/local/lib/python3.6/site-packages/controller

RUN useradd controller

USER controller

ENV PYTHONUNBUFFERED=true

ENTRYPOINT ["python", "-m", "controller"]
