ARG SIGOPT_GIT_HASH=d4257f9daf672139d7c3437c2f784eef4ae20f08

ARG UPGRADE_PACKAGES="expat libretls openssl"


FROM python:3.10.7-alpine3.16 AS updated-base

ARG UPGRADE_PACKAGES

RUN set -ex \
  ; apk del --purge krb5-conf krb5-libs \
  ; apk update --no-cache \
  ; apk add --upgrade --no-cache $UPGRADE_PACKAGES \
  ; :


FROM updated-base AS alpine-src

RUN set -ex \
  ; apk update --no-cache \
  ; apk add --no-cache alpine-sdk git \
  ; git clone --depth=1 --branch=3.16-stable git://git.alpinelinux.org/aports \
  ; mkdir -p /src \
  ; :

ARG UPGRADE_PACKAGES

RUN set -ex \
  ; for pkg in $UPGRADE_PACKAGES; do : \
    ; pkg="$(echo "$pkg" | awk -F= '{ print $1 }')" \
    ; cd /aports/*/$pkg \
    ; abuild -F fetch verify \
    ; cp -Lr /aports/*/$pkg /src/$pkg \
    ; done \
  ; :


FROM updated-base AS pip-reqs

ARG SIGOPT_GIT_HASH

# NOTE: the pip install attempts to install pypng==0.0.21 but for some reason that is not available in this container.
# The sigopt reqs ask for pypng>=0.0.20 so there should theoretically be no issue.
RUN set -ex \
  ; BUILD_PKGS="cargo git gcc libffi-dev musl-dev openssl-dev rust" \
  ; apk add --no-cache $BUILD_PKGS \
  ; mkdir -p /src \
  ; pip install --upgrade --no-cache-dir kubernetes==12.0.1 pypng==0.0.20 git+https://github.com/sigopt/sigopt-python@$SIGOPT_GIT_HASH \
  ; rm -rf /root/.cache \
  ; apk del --purge $BUILD_PKGS \
  ; :

RUN pip freeze > /pip-reqs.txt


FROM python:3.10.7 AS pip-src

COPY --from=pip-reqs /pip-reqs.txt /pip-reqs.txt

RUN cat /pip-reqs.txt | grep -v '@' | xargs -P8 pip download --no-binary=:all: --no-cache-dir -d /src

ARG SIGOPT_GIT_HASH

RUN set -ex \
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
