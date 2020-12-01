FROM ubuntu:16.04

RUN apt-get update \
    && apt-get install -yq --no-install-recommends \
       python3 \
       python3-pip \
       libpq-dev python3-dev build-essential \
    && python3 -m pip install --upgrade pip setuptools wheel
COPY requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt
RUN apt-get -o Dpkg::Options::='--force-confmiss' install --reinstall -y netbase
ENV FLASK_APP=project/__init__.py
ENV FLASK_ENV=development
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_DEBUG=1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/models
WORKDIR /app
EXPOSE 5000
