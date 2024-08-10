#!/bin/bash
# Librerias linux  para actualizar librerias que necesita aioRedis

apt-get update
apt-get install --reinstall build-essential -y
apt-get install --no-install-recommends lsb-release -y
apt-get clean all
