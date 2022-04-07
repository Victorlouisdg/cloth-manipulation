FROM ubuntu

# adapted from:
# https://github.com/nytimes/rd-blender-docker/blob/master/dist/3.0-cpu-ubuntu18.04/Dockerfile
# https://github.com/ikester/blender-docker


# RUN apt-get update && \
# 	apt-get install -y \
# 		curl \
# 		libfreetype6 \
# 		libglu1-mesa \
# 		libxi6 \
# 		libxrender1 \
# 		xz-utils && \
# 	apt-get -y autoremove && \
# 	rm -rf /var/lib/apt/lists/*

# The apt install gets stuck om "Geographic area:" without this var
ENV DEBIAN_FRONTEND=nonintercative

# The first packages here come from the nytimes docker container
# git is to clone my repos
# libglib2.0.0 was required for blenderproc installing opencv
RUN apt-get update && apt-get install -y \
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
    git \
    libglib2.0-0


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

WORKDIR "/usr/local/src"
RUN git clone https://github.com/Victorlouisdg/cloth-manipulation.git
RUN git clone https://github.com/airo-ugent/airo-blender-toolkit.git
RUN git clone https://github.com/DLR-RM/BlenderProc.git

WORKDIR "/usr/local/src"
RUN $BLENDER_PIP install -e airo-blender-toolkit
RUN $BLENDER_PIP install -e BlenderProc
RUN $BLENDER_PIP install -e cloth-manipulation

# VOLUME /media
# ENTRYPOINT ["/usr/local/blender/blender", "-b"]
