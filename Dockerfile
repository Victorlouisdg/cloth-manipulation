FROM ubuntu

# adapted from:
# https://github.com/nytimes/rd-blender-docker/blob/master/dist/3.0-cpu-ubuntu18.04/Dockerfile
# https://github.com/ikester/blender-docker

# The apt install gets stuck om "Geographic area:" without this var
ENV DEBIAN_FRONTEND=nonintercative


RUN apt-get update && apt-get install -y \
    # from the nytimes blender container, not sure if all are necessary
    curl \
    libopenexr-dev \
    bzip2 \
    build-essential \
    zlib1g-dev \
    libxmu-dev \
    libxi-dev \
    libxxf86vm-dev \
    libfontconfig1 \
    libxrender1 \
    libgl1-mesa-glx \
    xz-utils \
    # cloning my repos
    git \
    # cv2 during blenderproc install
    libglib2.0-0 \
    # provides add-apt-repository needed for Codim-IPC build
    software-properties-common


RUN mkdir "/root/Blender"
WORKDIR "/root/Blender"

ENV BLENDER_MAJOR 3.1
ENV BLENDER_VERSION 3.1.2
ENV BLENDER_PYTHON_VERSION 3.10
ENV BLENDER_NAME blender-$BLENDER_VERSION-linux-x64
ENV BLENDER_URL https://download.blender.org/release/Blender$BLENDER_MAJOR/$BLENDER_NAME.tar.xz

RUN echo $BLENDER_URL

# Example used -L option for curl, but doesn't seem necessary
# Pipe curl output directly to tar to unzip
RUN curl -L $BLENDER_URL | tar xJ

ENV BLENDER_DIR /root/Blender/$BLENDER_NAME
ENV BLENDER_PYTHON_BIN_DIR $BLENDER_DIR/$BLENDER_MAJOR/python/bin
ENV BLENDER_PYTHON $BLENDER_PYTHON_BIN_DIR/python${BLENDER_PYTHON_VERSION}
RUN $BLENDER_PYTHON -m ensurepip
ENV BLENDER_PIP $BLENDER_PYTHON_BIN_DIR/pip3
# Gets rid of the warning:
RUN $BLENDER_PIP install --upgrade pip
ENV PATH="$BLENDER_DIR:$PATH"

WORKDIR "/root"

# Deps mostly for Codim-IPC build but one of wandbs deps also required Python.h
RUN add-apt-repository ppa:deadsnakes/ppa && apt update
RUN apt-get install -y \
    libpython3.10-dev \
    cmake \
    freeglut3-dev \
    libeigen3-dev \
    libboost-all-dev

# Without this the setproctitle build fails
ENV PYTHON_INCLUDE "/usr/include/python$BLENDER_PYTHON_VERSION/"
ENV CPATH="$PYTHON_INCLUDE:$CPATH"

# Install C-IPC first because the build takes a while
RUN git clone https://github.com/Victorlouisdg/Codim-IPC.git
RUN $BLENDER_PIP install -e Codim-IPC


RUN git clone https://github.com/DLR-RM/BlenderProc.git
RUN $BLENDER_PIP install -e BlenderProc

RUN git clone https://github.com/airo-ugent/airo-blender-toolkit.git
RUN $BLENDER_PIP install -e airo-blender-toolkit

# Make folder to download assets in later
RUN mkdir /root/assets

# The first time you import blenderproc it installs several dependencies
RUN blender -b -P /root/airo-blender-toolkit/tests/test_blenderproc_import.py

RUN git clone https://github.com/Victorlouisdg/cloth-manipulation.git
RUN $BLENDER_PIP install -e cloth-manipulation
WORKDIR "/root/cloth-manipulation"

# VOLUME /media
# ENTRYPOINT ["/usr/local/blender/blender", "-b"]
