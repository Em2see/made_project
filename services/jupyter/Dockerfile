FROM jupyter/base-notebook:latest

ENV BUILD_DEPS="build-essential" \
    APP_DEPS="curl libpq-dev python3-dev"

USER root

COPY ./requirements.txt requirements.txt

#RUN pip install "psycopg2-binary" && pip install -r requirements.txt 

RUN apt-get -y update \
    && apt-get install -y ${BUILD_DEPS} ${APP_DEPS} --no-install-recommends \
    && pip install -r requirements.txt \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /usr/share/doc && rm -rf /usr/share/man \
    && apt-get purge -y --auto-remove ${BUILD_DEPS} \
    && apt-get clean

ENV HOME=/

EXPOSE 8888