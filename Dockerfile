FROM python:3.11-slim
MAINTAINER Mantikor <straltsou.siarhei@gmail.com>

RUN ["apt-get", "update"]
RUN ["apt-get", "upgrade", "-y"]
RUN mkdir /opt/ts_series_updater
COPY requirements.txt /opt/ts_series_updater
RUN ["pip", "install", "-r", "/opt/ts_series_updater/requirements.txt"]
COPY series_updater.py /opt/ts_series_updater/
# COPY config.yaml /opt/ts_series_updater/
WORKDIR /opt/ts_series_updater/

# CMD ["python", "series_updater.py", "--litrcc 20000000-ffff-ffff-ffff-200000000000", "--ts_url http://192.168.1.2", "--settings config.yaml"]
