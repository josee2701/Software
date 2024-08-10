# Instala la imagen de Python
FROM python:3.10-slim-bullseye
# Establece las variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV ACCEPT_EULA=Y
# Define el directorio de trabajo
WORKDIR /gps-mobile
# Copia el contexto de la aplicacion en el directorio de trabajo.
# Excluye los archivos señalados en .dockerfile
COPY requirements.txt /gps-mobile/requirements.txt
RUN echo "deb [trusted=yes] http://deb.debian.org/debian stable main" > /etc/apt/sources.list
RUN apt-get update; \
    apt-get -y upgrade
RUN apt -y install curl
RUN apt -y install gcc
RUN apt -y install g++
RUN apt -y install build-essential
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
&& apt-get update
RUN apt-get install -y --no-install-recommends --allow-unauthenticated msodbcsql18
RUN apt-get install -y --no-install-recommends --allow-unauthenticated mssql-tools18
RUN echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
RUN export PATH="$PATH:/opt/mssql-tools18/bin"
RUN apt-get install -y unixodbc-dev
RUN apt-get install -y libgssapi-krb5-2
# Instalación de dependencias apt
RUN apt-get update
RUN apt-get install --reinstall build-essential -y
RUN apt-get install --no-install-recommends lsb-release -y
RUN apt-get clean all
# Instalación de dependencias de Python
RUN python -m venv /opt/venv
RUN /opt/venv/bin/pip install --upgrade pip \
&& /opt/venv/bin/pip install wheel \
&& /opt/venv/bin/pip install --no-cache-dir -r /gps-mobile/requirements.txt
# RUN pip install --upgrade pip \
# && pip install --no-cache-dir -r /gps-mobile/requirements.txt
# instalacion de la libreria de internacionalizacion
RUN apt-get install gettext -y
COPY . /gps-mobile
# RUN /opt/venv/bin/python manage.py collectstatic
RUN chmod +x entrypoint.sh
RUN chmod +x utils/migrations.sh
# Inicia el servidor de DJango
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
