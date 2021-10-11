FROM python:3.9.6-alpine3.14 AS updated-base

RUN apk del krb5-conf krb5-libs

# NOTE: packages to update are busybox, libretls and openssl.
# all dependencies and exact versions are mentioned here so that we can ensure the correct sources are downloaded for licensing.
ENV UPDATED_PKGS "busybox=1.33.1-r3 libcrypto1.1=1.1.1l-r0 libretls=3.3.3p1-r2 libssl1.1=1.1.1l-r0 openssl=1.1.1l-r0 ssl_client=1.33.1-r3"

RUN set -ex \
  ; apk update --no-cache \
  ; apk add --upgrade --no-cache $UPDATED_PKGS \
  ; :


FROM updated-base AS alpine-src

RUN apk update --no-cache

RUN apk add --no-cache alpine-sdk git

RUN git clone --depth=1 --branch=v3.14.0 git://git.alpinelinux.org/aports

RUN mkdir -p /src

# NOTE: https://pkgs.alpinelinux.org/packages shows that for each of the updated packages these source packages are listed as the origin.
ENV SRC_PKGS "busybox libretls openssl"

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
  ; mkdir -p /src \
  ; pip install --upgrade --no-cache-dir kubernetes==12.0.1 pypng==0.0.20 git+https://github.com/sigopt/sigopt-python@d5c71dca6b754405f644e8f89214d823aa2e3f58 \
  ; apk del --purge $BUILD_PKGS \
  ; :

RUN apk del apk-tools

COPY --from=alpine-src /src/ /src/

RUN pip freeze | grep -v '@' | xargs pip download --no-binary=:all: --no-cache-dir -d /src

COPY controller /usr/local/lib/python3.9/site-packages/controller

RUN adduser -S controller

USER controller

ENV PYTHONUNBUFFERED=true

ENTRYPOINT ["python", "-m", "controller"]
