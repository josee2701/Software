from django.db import DatabaseError, connection


def fetch_all_dataplan(company, user):
    with connection.cursor() as cursor:
        # Asegurarse de que 'company' es del tipo correcto, por ejemplo, un entero
        company_id = int(company.id)  # Convertir a entero si es necesario
        user_id = int(user.id)

        # Llamada al procedimiento almacenado con el parámetro correctamente formateado
        cursor.execute(
            "EXEC [dbo].[ListDataplanByCompany] @CompanyId=%s , @UserId=%s",
            [company_id, user_id],
        )

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in rows]


def fetch_all_simcards(company, user):
    with connection.cursor() as cursor:
        # Asegurarse de que 'company' es del tipo correcto, por ejemplo, un entero
        company_id = int(company.id)  # Convertir a entero si es necesario
        user_id = int(user.id)

        # Llamada al procedimiento almacenado con el parámetro correctamente formateado
        cursor.execute(
            "EXEC [dbo].[ListSimcardsByCompany] @CompanyId=%s , @UserId=%s",
            [company_id, user_id],
        )

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    
def fetch_all_device(company, user):
    with connection.cursor() as cursor:
        # Asegurarse de que 'company' es del tipo correcto, por ejemplo, un entero
        company_id = int(company.id)  # Convertir a entero si es necesario

        # Llamada al procedimiento almacenado con el parámetro correctamente formateado
        cursor.execute("EXEC [dbo].[ListDeviceByCompany] @CompanyId=%s, @UserId=%s", [company_id, user])

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in rows]


def fetch_all_sending_commands(company_id, user_id):
    try:
        with connection.cursor() as cursor:
            # Consulta que selecciona todos los comandos enviados por compañía y sus proveedores
            cursor.execute(
                "EXEC [dbo].[ListSendingCommandsdByCompanyAndUser] @CompanyId=%s , @UserId =%s",
                [company_id, user_id],
            )
            rows = cursor.fetchall()
            if rows:
                # Usar cursor.description para obtener los nombres de las columnas
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            else:
                cursor.execute(
                    """
                        EXEC [dbo].[ListSendingCommandsdByCompany] @CompanyId=%s, @UserId =%s
                    """,
                    [company_id, user_id],
                )
                rows = cursor.fetchall()
                # Usar cursor.description para obtener los nombres de las columnas
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in rows]

    except DatabaseError as e:
        # Manejar el error de base de datos aquí
        print("Error de base de datos:", e)
        return None

    except Exception as e:
        print("error al realizar la consulta fetch_all_sending_commands:", e)
        return None


def fetch_all_response_commands(company_id, user_id):
    try:
        with connection.cursor() as cursor:
            # Consulta que selecciona todas respuestas de comandos por compañía y sus proveedores
            cursor.execute(
                "EXEC [dbo].[ListResponseCommandsdByCompanyAndUser] @CompanyId=%s , @UserId =%s",
                [company_id, user_id],
            )
            rows = cursor.fetchall()
            if rows:
                # Usar cursor.description para obtener los nombres de las columnas
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            else:
                cursor.execute(
                    """
                        EXEC [dbo].[ListResponseCommandsdByCompany] @CompanyId=%s, @UserId =%s
                    """,
                    [company_id, user_id],
                )
                rows = cursor.fetchall()
                # Usar cursor.description para obtener los nombres de las columnas
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in rows]

    except DatabaseError as e:
        # Manejar el error de base de datos aquí
        print("Error de base de datos:", e)
        return None

    except Exception as e:
        print("error al realizar la consulta fetch_all_sending_commands:", e)
        return None
    
def fetch_all_geozones(user_company_id, user):
    try:
        with connection.cursor() as cursor:
            # Consulta que selecciona todas las geozonas sin filtrar por compañía

            cursor.execute(
                "EXEC [dbo].[ListGeoZonesByCompany] @CompanyId=%s, @UserId =%s", [user_company_id, user]
            )  # Ejecuta la consulta sin parámetros
            rows = cursor.fetchall()

            # Usar cursor.description para obtener los nombres de las columnas
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    except DatabaseError as e:
        # Manejar el error de base de datos aquí
        print("Error de base de datos:", e)
        return []
    
    except Exception as e:
        print("error al realizar la consulta fetch_all_geozones:", e)
        return []
    

def ListVehicleGroupsByCompany(company_id):
    try:
        with connection.cursor() as cursor:
            # Consulta que selecciona todos los grupos por compañía y sus proveedores
            cursor.execute(
                "EXEC [dbo].[ListVehicleGroupsByCompany] @company_id=%s", [company_id]
            )
            rows = cursor.fetchall()

            # Usar cursor.description para obtener los nombres de las columnas
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    except DatabaseError as e:
        # Manejar el error de base de datos aquí
        print("Error de base de datos:", e)
        return None

    except Exception as e:
        print("error al realizar la consulta ListVehicleGroupsByCompany:", e)
        return None


def ListVehicleByUserAndCompany(company_id, user_id):
    try:
        with connection.cursor() as cursor:
            # Consulta que selecciona todos los vehicles por compañía y sus proveedores
            cursor.execute(
                "EXEC [dbo].[ListVehicleByUserAndCompany] @CompanyId=%s , @UserId =%s",
                [company_id, user_id],
            )
            rows = cursor.fetchall()
            if rows:
                # Usar cursor.description para obtener los nombres de las columnas
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            else:
                cursor.execute(
                    """
                        EXEC [dbo].[ListVehicleByCompany] @CompanyId=%s
                    """,
                    [company_id],
                )
                rows = cursor.fetchall()
                # Usar cursor.description para obtener los nombres de las columnas
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in rows]

    except DatabaseError as e:
        # Manejar el error de base de datos aquí
        print("Error de base de datos:", e)
        return []
    
    except Exception as e:
        print("error al realizar la consulta ListVehicleByUserAndCompany:", e)
        return []
    

def ListDeviceByCompany(company_id, user_id):
    try:
        with connection.cursor() as cursor:
            # Consulta que selecciona todos los devices por compañía y sus proveedores
            cursor.execute("EXEC [dbo].[ListDeviceByCompany] @CompanyId=%s, @UserId=%s", [company_id, user_id])
            rows = cursor.fetchall()

            # Usar cursor.description para obtener los nombres de las columnas
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    except DatabaseError as e:
        # Manejar el error de base de datos aquí
        print("Error de base de datos:", e)
        return None

    except Exception as e:
        print("error al realizar la consulta ListDeviceByCompany:", e)
        return None
