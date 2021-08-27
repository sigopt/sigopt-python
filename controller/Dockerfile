FROM python:3.9.6-alpine3.14 AS updated-base

ENV UPDATED_PKGS "busybox krb5-libs libcrypto1.1 libretls libssl1.1 openssl ssl_client"

RUN set -ex \
  ; apk update --no-cache \
  ; apk add --upgrade --no-cache $UPDATED_PKGS \
  ; :


FROM updated-base AS alpine-src

RUN apk update --no-cache

RUN apk add --no-cache alpine-sdk git

RUN git clone --depth=1 --branch=v3.14.0 git://git.alpinelinux.org/aports

RUN mkdir -p /src

ENV SRC_PKGS "busybox krb5 libretls openssl"

RUN set -ex \
  ; for pkg in $SRC_PKGS \
    ; do cd /aports/*/$pkg \
    ; abuild -F fetch verify \
    ; cp -Lr /aports/*/$pkg /src/$pkg \
    ; done \
  ; :


FROM updated-base

# NOTE: the pip install attempts to install pypng==0.0.21 but for some reason that is not available in this container.
# The sigopt reqs ask for pypng>=0.0.20 so there should theoretically be no issue.
RUN set -ex \
  ; BUILD_PKGS="cargo git gcc libffi-dev musl-dev openssl-dev rust" \
  ; apk add --no-cache $BUILD_PKGS \
  ; pip install --upgrade --no-cache-dir git+https://github.com/sigopt/sigopt-python.git@sj/main \
  ; mkdir -p /src \
  ; pip install --no-cache-dir kubernetes==12.0.1 pypng==0.0.20 git+https://github.com/sigopt/sigopt-python.git@sj/main \
  ; apk del --purge $BUILD_PKGS \
  ; :

RUN apk del apk-tools

COPY --from=alpine-src /src/ /src/

COPY controller /usr/local/lib/python3.9/site-packages/controller

RUN adduser -S controller

USER controller

ENV PYTHONUNBUFFERED=true

ENTRYPOINT ["python", "-m", "controller"]
