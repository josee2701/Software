from datetime import datetime, timedelta

import psycopg2
from decouple import config


def connect_db():
    params = {
        "dbname": config("POSTGRES_NAME"),
        "user": config("POSTGRES_USER"),
        "password": config("POSTGRES_PASSWORD"),
        "host": config("POSTGRES_HOST"),
        "port": config("POSTGRES_PORT", cast=int),
        "sslmode": config("POSTGRES_SSLMODE"),
    }
    try:
        connection = psycopg2.connect(**params)
        return connection
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None


class GeocodingService:
    def __init__(self):
        self.connection = None

    def connect(self):
        if not self.connection:
            self.connection = connect_db()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def rev_geocode(self, latitude, longitude):
        if not self.connection:
            return None
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT public.rev_geocode_gpsmobile(%s, %s)",
                [longitude, latitude],
            )
            return cursor.fetchone()[0]

    @staticmethod
    def adjust_dates(date_str, timezone_offset):
        utc_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
        local_date = utc_date - timedelta(minutes=timezone_offset)
        return local_date.strftime("%Y-%m-%d %H:%M:%S")
