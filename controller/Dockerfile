FROM python:3.9.6-alpine3.14 AS deps

RUN set -ex \
  ; apk update --no-cache \
  ; apk add --upgrade --no-cache busybox libretls openssl krb5-libs \
  ; :


FROM deps AS srcs

RUN mkdir -p /dist

RUN set -ex \
  ; apk add --no-cache git \
  ; git clone --depth=1 --branch=v3.14.0 git://git.alpinelinux.org/aports /aports \
  ; cp -r /aports /dist/aports \
  ; apk del --purge git \
  ; :

RUN apk add --no-cache alpine-sdk

RUN set -ex \
  ; apk list -I -q | awk '{ print $3 }' | sed 's/[{}]//g' | grep -v '^\.' | while read pkg \
    ; do cd /aports/*/$pkg \
    ; abuild -F fetch verify \
    ; cp -Lr src /dist/$pkg \
    ; done \
  ; :


FROM deps

RUN set -ex \
  ; BUILD_DEPS="cargo git gcc libffi-dev musl-dev openssl-dev rust" \
  ; apk add --no-cache $BUILD_DEPS \
  ; pip install --no-cache-dir kubernetes==12.0.1 git+https://github.com/sigopt/sigopt-python.git@sj/main \
  ; mkdir -p /src \
  ; pip freeze | grep -v '@' | xargs pip download --no-cache-dir --no-binary=:all: --dest=/src \
  ; apk del --purge $BUILD_DEPS \
  ; :

RUN apk del apk-tools

COPY --from=srcs /dist/ /src/

COPY controller /usr/local/lib/python3.9/site-packages/controller

RUN adduser -S controller

USER controller

ENV PYTHONUNBUFFERED=true

ENTRYPOINT ["python", "-m", "controller"]
