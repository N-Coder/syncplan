FROM debian:bullseye

RUN apt-get update && apt-get install -y \
    build-essential \
    ccache \
    cmake \
    cmake-curses-gui \
    git \
    htop \
    libunwind-dev \
    python3 \
    python3-pip \
    sed \
    slurm-wlm \
    tar \
    time \
    unzip \
    vim \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root

CMD /bin/bash
