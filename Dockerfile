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


ENV BLENDER_MAJOR 3.1
ENV BLENDER_VERSION 3.1.0
ENV BLENDER_PYTHON_VERSION 3.10
ENV BLENDER_NAME blender-$BLENDER_VERSION-linux-x64
ENV BLENDER_URL https://download.blender.org/release/Blender$BLENDER_MAJOR/$BLENDER_NAME.tar.xz

WORKDIR "/usr/local"
RUN echo $BLENDER_URL

# Example used -L option for curl, but doesn't seem necessary
# Pipe curl output directly to tar to unzip
RUN curl -L $BLENDER_URL | tar xJ

ENV BLENDER_DIR /usr/local/$BLENDER_NAME
ENV BLENDER_PYTHON_BIN_DIR $BLENDER_DIR/$BLENDER_MAJOR/python/bin
ENV BLENDER_PYTHON $BLENDER_PYTHON_BIN_DIR/python${BLENDER_PYTHON_VERSION}
RUN $BLENDER_PYTHON -m ensurepip
ENV BLENDER_PIP $BLENDER_PYTHON_BIN_DIR/pip3
# Gets rid of the warning:
RUN $BLENDER_PIP install --upgrade pip
ENV PATH="$BLENDER_DIR:$PATH"

# Make folder to download assets in later
RUN mkdir /root/assets

WORKDIR "/usr/local/src"
RUN git clone https://github.com/Victorlouisdg/cloth-manipulation.git
RUN git clone https://github.com/airo-ugent/airo-blender-toolkit.git
RUN git clone https://github.com/DLR-RM/BlenderProc.git

# Missed dependency of trimesh
RUN $BLENDER_PIP install rtree

RUN $BLENDER_PIP install -e airo-blender-toolkit
RUN $BLENDER_PIP install -e BlenderProc
RUN $BLENDER_PIP install -e cloth-manipulation

WORKDIR "/usr/local/src/cloth-manipulation/Codim-IPC"
RUN mkdir build && cd build && rm -rf CMakeCache.txt
WORKDIR "/usr/local/src/cloth-manipulation/Codim-IPC/build"

# Codim-IPC build
RUN add-apt-repository ppa:deadsnakes/ppa && apt update
RUN apt-get install -y \
    libpython3.10-dev \
    cmake \
    freeglut3-dev \
    libeigen3-dev \
    libboost-all-dev

# python3-dev \


ENV PYTHON_LIBS "/usr/lib/libpython$BLENDER_PYTHON_VERSION.so"
ENV PYTHON_INCLUDE "/usr/include/python$BLENDER_PYTHON_VERSION/"

RUN cmake -DCMAKE_BUILD_TYPE=Release \
    -DPYTHON_EXECUTABLE:FILEPATH=$BLENDER_PYTHON \
    -DPYTHON_LIBRARIES=$PYTHON_LIBS \
    -DPYTHON_INCLUDE_DIRS=$PYTHON_INCLUDE \
    ..

RUN make -j 12

# VOLUME /media
# ENTRYPOINT ["/usr/local/blender/blender", "-b"]
