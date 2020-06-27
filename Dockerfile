FROM python:3.6-slim

COPY ./requirements.txt /requirements.txt

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y apt-utils
RUN apt-get install -y net-tools
RUN pip3 install -r requirements.txt

COPY . /

ENV FALCONWEATHER_DOCKERIZED True
ENV FALCONWEATHER_DB_PASSWORD f4lc0nw34th3r
ENV FALCONWEATHER_SITE http://weather.8harvest.net

CMD [ "./go.sh" ]
