#!/bin/bash

# Navega al directorio donde se encuentra el manage.py de Django
cd /gps-mobile/

# Recolecta los archivos estáticos
/opt/venv/bin/python manage.py collectstatic --no-input

# Aplica las migraciones existentes
/opt/venv/bin/python manage.py showmigrations
/opt/venv/bin/python manage.py makemigrations --no-input
/opt/venv/bin/python manage.py migrate --no-input

# Carga los datos iniciales desde los fixtures
/opt/venv/bin/python manage.py loaddata apps/whitelabel/fixtures/whitelabel_data.json
/opt/venv/bin/python manage.py loaddata apps/realtime/fixtures/realtime.json
/opt/venv/bin/python manage.py loaddata apps/realtime/fixtures/uec_fixtures.json
/opt/venv/bin/python manage.py loaddata apps/authentication/fixtures/authentication.json
/opt/venv/bin/python manage.py loaddata apps/checkpoints/fixtures/itmes.json
/opt/venv/bin/python manage.py loaddata apps/events/fixtures/events.json

# Agregar cualquier otra tarea de gestión necesaria aquí
