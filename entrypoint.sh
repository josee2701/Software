#!/bin/bash
APP_PORT=${PORT:-8000}
cd /gps-mobile/
/opt/venv/bin/daphne -b 0.0.0.0 -p ${APP_PORT} config.asgi:application
