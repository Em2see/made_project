FROM python:3.7-stretch
COPY requirements.txt /requirements.txt

ENV BUILD_DEPS="build-essential" \
    APP_DEPS="curl libpq-dev"

RUN apt-get update \
    && apt-get install -y ${BUILD_DEPS} ${APP_DEPS} --no-install-recommends

RUN pip install -r /requirements.txt \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /usr/share/doc && rm -rf /usr/share/man \
    && apt-get purge -y --auto-remove ${BUILD_DEPS} \
    && apt-get clean

#RUN apt-get -o Dpkg::Options::='--force-confmiss' install --reinstall -y netbase

ENV FLASK_APP=project/__init__.py
ENV FLASK_ENV=development
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_DEBUG=1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/models
WORKDIR /app
EXPOSE 5000
