#!/bin/bash
# actualzacion del pip e Instalacion de los requirements

pip install --upgrade pip \
pip install wheel \
pip install --no-cache-dir -r /gps-mobile/requirements.txt
