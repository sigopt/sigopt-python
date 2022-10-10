ARG SIGOPT_GIT_HASH=d4257f9daf672139d7c3437c2f784eef4ae20f08

ARG BUILD_PACKAGES="cargo=1.60.0-r2 git=2.36.2-r0 gcc=11.2.1_git20220219-r2 libffi-dev=3.4.2-r1 musl-dev=1.2.3-r0 openssl-dev=1.1.1q-r0 rust=1.60.0-r2"
ARG UPGRADE_PACKAGES="expat=2.4.9-r0 libretls=3.5.2-r0 openssl=1.1.1q-r0"


FROM python:3.10.7-alpine3.16 AS updated-base

SHELL ["/bin/ash", "-ex", "-o", "pipefail", "-c"]

ARG UPGRADE_PACKAGES

# hadolint ignore=DL3018
RUN : \
  ; apk del --purge krb5-conf krb5-libs \
  ; apk update --no-cache \
  ; apk add --upgrade --no-cache $UPGRADE_PACKAGES \
  ; :


FROM updated-base AS alpine-src

SHELL ["/bin/ash", "-ex", "-o", "pipefail", "-c"]

ARG UPGRADE_PACKAGES

RUN : \
  ; apk update --no-cache \
  ; apk add --no-cache alpine-sdk=1.0-r1 git=2.36.2-r0 \
  ; git clone --depth=1 --branch=3.16-stable git://git.alpinelinux.org/aports \
  ; mkdir -p /src \
  ; :

# hadolint ignore=DL3003
RUN : \
  ; echo "$UPGRADE_PACKAGES" | awk -F= '{ print $1 }' | while read -r pkg; do : \
    ; cd /aports/*/"$pkg" || exit 1 \
    ; abuild -F fetch verify \
    ; cp -Lr /aports/*/"$pkg" /src/"$pkg" \
    ; done \
  ; :


FROM updated-base AS pip-reqs

SHELL ["/bin/ash", "-ex", "-o", "pipefail", "-c"]

ARG BUILD_PACKAGES
ARG SIGOPT_GIT_HASH

# NOTE: the pip install attempts to install pypng==0.0.21 but for some reason that is not available in this container.
# The sigopt reqs ask for pypng>=0.0.20 so there should theoretically be no issue.
# hadolint ignore=DL3018
RUN : \
  ; apk add --no-cache $BUILD_PACKAGES \
  ; mkdir -p /src \
  ; pip install --upgrade --no-cache-dir kubernetes==12.0.1 pypng==0.0.20 git+https://github.com/sigopt/sigopt-python@$SIGOPT_GIT_HASH \
  ; rm -rf /root/.cache \
  ; echo "$BUILD_PACKAGES" | awk -F= '{ print $1 }' | xargs apk del --purge \
  ; :

RUN pip freeze > /pip-reqs.txt


FROM python:3.10.7 AS pip-src

SHELL ["/bin/bash", "-ex", "-o", "pipefail", "-c"]

COPY --from=pip-reqs /pip-reqs.txt /pip-reqs.txt

RUN : \
  ; grep -v '@' </pip-reqs.txt | xargs -P8 pip download --no-binary=:all: --no-cache-dir -d /src \
  ; :

ARG SIGOPT_GIT_HASH

RUN : \
  ; curl -fSsLo /src/sigopt-python@$SIGOPT_GIT_HASH.tar https://github.com/sigopt/sigopt-python/tarball/$SIGOPT_GIT_HASH \
  ; :


FROM pip-reqs

RUN apk del apk-tools

COPY --from=alpine-src /src/ /src/
COPY --from=pip-src /src/ /src/

COPY controller /usr/local/lib/python3.10/site-packages/controller

RUN adduser -S controller

USER controller

ENV PYTHONUNBUFFERED=true

ENTRYPOINT ["python", "-m", "controller"]
