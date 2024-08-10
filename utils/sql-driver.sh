#!/bin/bash
# Instala el driver Microsoft ODBC para SQL Server
# Explicacion:
# https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver15
# Correcion de errores para instalar en imagen python bullseye
# https://stackoverflow.com/questions/51888064/install-odbc-driver-in-alpine-linux-docker-container

apt -y update
apt -y upgrade
apt -y install curl gcc g++ build-essential
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Optional: for bcp and sqlcmd
apt-get update
apt-get install -y --no-install-recommends --allow-unauthenticated msodbcsql18
apt-get install -y --no-install-recommends --allow-unauthenticated mssql-tools18
echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
export PATH="$PATH:/opt/mssql-tools18/bin"

# Optional: for unixODBC development headers
apt-get install -y unixodbc-dev

# Optional: kerberos library for debian-slim distributions
apt-get install -y libgssapi-krb5-2
