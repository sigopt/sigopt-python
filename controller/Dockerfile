FROM alpine:3.14.0 AS alpine-src

RUN apk add --no-cache alpine-sdk git

RUN git clone --depth=1 --branch=v3.14.0 git://git.alpinelinux.org/aports

RUN mkdir -p /src

RUN set -ex \
  ; for pkg in busybox libretls openssl \
    ; do cd /aports/main/$pkg \
    ; abuild -F fetch verify \
    ; mv /aports/main/$pkg /src/$pkg \
    ; done \
  ; :

FROM python:3.9.6-alpine3.14

RUN set -ex \
  ; apk update --no-cache \
  ; apk add --upgrade --no-cache busybox libretls openssl \
  ; :

RUN set -ex \
  ; apk add --no-cache cargo git gcc libffi-dev musl-dev openssl-dev rust \
  ; pip install --no-cache-dir kubernetes==12.0.1 git+https://github.com/sigopt/sigopt-python.git@sj/main \
  ; mkdir -p /src \
  ; pip freeze | grep -v '@' | xargs pip download --no-cache-dir --no-binary=:all: --dest=/src \
  ; apk del --purge cargo git gcc libffi-dev musl-dev openssl-dev rust \
  ; :

RUN apk del apk-tools

COPY --from=alpine-src /src/ /

COPY controller /usr/local/lib/python3.6/site-packages/controller

RUN adduser -S controller

USER controller

ENV PYTHONUNBUFFERED=true

ENTRYPOINT ["python", "-m", "controller"]
