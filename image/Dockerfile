FROM python:3.12-slim-bookworm

ARG BRIDGE_VERSION

LABEL gg.serverk.bridge.version="${BRIDGE_VERSION}"

LABEL org.opencontainers.image.source="https://github.com/serverkgg/bot-python"

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      tini ca-certificates tzdata git util-linux ffmpeg; \
    rm -rf /var/lib/apt/lists/*; \
    if getent passwd 1000 > /dev/null; then \
      userdel -r "$(getent passwd 1000 | cut -d: -f1)"; \
    fi; \
    if getent group 1000 > /dev/null; then \
      groupdel "$(getent group 1000 | cut -d: -f1)"; \
    fi; \
    groupadd -g 1000 container; \
    useradd -M -d /home/container -u 1000 -g 1000 -s /usr/sbin/nologin container; \
    mkdir -p /home/container /serverk/run; \
    python3 --version; \
    git --version

ENV TZ=UTC \
    HOME=/home/container \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_INPUT=1

COPY dist/bridge /serverk/bridge

COPY image/launcher.py image/git-askpass image/detect.json /serverk/

RUN chmod 0755 /serverk/bridge /serverk/git-askpass; \
    chmod 0644 /serverk/launcher.py /serverk/detect.json

WORKDIR /home/container

ENTRYPOINT ["/usr/bin/tini", "--", "/serverk/bridge"]
