FROM python:3.6.12

RUN pip install --no-cache-dir kubernetes==12.0.1 git+https://github.com/sigopt/sigopt-python.git@sj/main

RUN set -ex \
  ; mkdir -p /src \
  ; pip freeze | grep -v '@' | xargs pip download --no-binary=:all: --dest=/src \
  ; :

COPY controller /usr/local/lib/python3.6/site-packages/controller

RUN useradd controller

USER controller

ENV PYTHONUNBUFFERED=true

ENTRYPOINT ["python", "-m", "controller"]
