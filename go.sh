#!/bin/bash

export DOCKER_HOST_IP=$(route -n | awk '/UG[ \t]/{print $2}')

gunicorn falconweather:api --workers=3 -b 0.0.0.0:8000
