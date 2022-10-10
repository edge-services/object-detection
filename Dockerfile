
## docker build -t sinny777/object-detection:latest .

# DISPLAY=:0 docker run --rm -it --name detection  \
# --privileged \
# --device /dev/video0 \
# --device /dev/mem   \
# --device /dev/vchiq \
# -v /opt/vc:/opt/vc  \
# -v /tmp:/tmp \
# sinny777/object-detection:latest

ARG ARCH=arm64v8
ARG PYTHON_VERSION=3.8.13
ARG OS=slim-buster
# ARG DEBIAN_FRONTEND=noninteractive
# ARG DEBCONF_NOWARNINGS="yes"

FROM ${ARCH}/python:${PYTHON_VERSION}-${OS}

USER root

LABEL org.label-schema.build-date=${BUILD_DATE} \
    org.label-schema.docker.dockerfile=".docker/Dockerfile.arm" \
    org.label-schema.license="Apache-2.0" \
    org.label-schema.name="EdgeDetection" \
    org.label-schema.version=${BUILD_VERSION} \
    org.label-schema.description="Edge Services - Detection Service" \
    org.label-schema.url="https://github.com/edge-services/detection" \
    org.label-schema.vcs-ref=${BUILD_REF} \
    org.label-schema.vcs-type="Git" \
    org.label-schema.vcs-url="https://github.com/edge-services/detection" \
    org.label-schema.arch=${ARCH} \
    maintainer="Gurvinder Singh <sinny777@gmail.com>"

RUN apt update && \
    apt -qy install --no-install-recommends \
    sudo unzip curl nano make \
    build-essential cmake pkg-config \
    gcc g++ \
    openssl \
    openssh-client \
    libssl-dev \
    ffmpeg libsm6 libxext6 fswebcam libgconf2-dev \
    # cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get -y autoremove

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PATH="$PATH:/opt/vc/bin"
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/vc/lib:/usr/local/lib:/opt/venv/lib:/usr/lib:/lib:/usr/share:/usr/share
# ENV LD_LIBRARY_PATH=/usr/local/lib/python3.8/site-packages/cv2/qt/plugins
ENV TZ Asia/Kolkata
ENV PYTHONUNBUFFERED=1

RUN apt update

# RUN addgroup --gid 1001 --system app && \
#     adduser --no-create-home --shell /bin/false --disabled-password --uid 1001 --system --group app \
#     && chgrp -R 0 /opt/venv/lib \
#     && chmod -R g=u /opt/venv/lib

COPY requirements.txt .
COPY setup.sh .

RUN echo "/opt/vc/lib" > /etc/ld.so.conf.d/00-vcms.conf \
    && ldconfig \
    && python -m pip install pip --upgrade && pip install --no-cache-dir -r requirements.txt

RUN chmod 755 /app/setup.sh && \
    bash /app/setup.sh -d data -a ${ARCH}

COPY ./app .

# ADD 00-vmcs.conf /etc/ld.so.conf.d/

# USER app

CMD ["python", "-u", "app.py"]