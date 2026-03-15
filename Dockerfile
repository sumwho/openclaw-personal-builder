FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        build-essential \
        ca-certificates \
        cmake \
        gdb \
        git \
        libsdl2-dev \
        libsdl2-image-dev \
        libsdl2-mixer-dev \
        libsdl2-ttf-dev \
        libgl1-mesa-dev \
        libglu1-mesa-dev \
        libopenal-dev \
        ninja-build \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

ARG USERNAME=builder
ARG USER_UID=1000
ARG USER_GID=1000

RUN groupadd --gid ${USER_GID} ${USERNAME} \
    && useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME}

USER ${USERNAME}
WORKDIR /workspace

CMD ["bash"]

