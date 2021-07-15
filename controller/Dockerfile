FROM python:3.6.12-alpine

RUN set -ex \
  ; apk add --no-cache cargo git gcc libffi-dev musl-dev openssl-dev rust \
  ; pip install --no-cache-dir kubernetes==12.0.1 git+https://github.com/sigopt/sigopt-python.git@sj/main \
  ; mkdir -p /src \
  ; pip freeze | grep -v '@' | xargs pip download --no-binary=:all: --dest=/src \
  ; apk del cargo git gcc libffi-dev musl-dev openssl-dev rust \
  ; :


COPY controller /usr/local/lib/python3.6/site-packages/controller

RUN adduser -S controller

USER controller

ENV PYTHONUNBUFFERED=true

ENTRYPOINT ["python", "-m", "controller"]
