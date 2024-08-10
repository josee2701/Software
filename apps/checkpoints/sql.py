from django.db import DatabaseError, connection


def get_drivers_list(user_company_id, user_id, search_query=None):
    try:
        with connection.cursor() as cursor:
            # Consulta que selecciona todos los conductores por compañía y sus proveedores
            cursor.execute(
                "EXEC [dbo].[ListCheckpointsDrivers] @CompanyId=%s, @UserId=%s, @SearchQuery=%s",
                [user_company_id, user_id, search_query],
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
        print("error al realizar la consulta get_drivers_list:", e)
        return []


def getCompanyScoresByCompanyAndUser(company_id, user_id, search_query=None):
    try:
        with connection.cursor() as cursor:
            # Consulta que selecciona todas las compañias por compañía y sus proveedores
            cursor.execute(
                "EXEC [dbo].[ListCompanyScoresByCompanyAndUser] @CompanyId=%s, @UserId=%s, @SearchQuery=%s",
                [company_id, user_id, search_query],
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
        print("error al realizar la consulta ListCompanyScoresByCompanyAndUser:", e)
        return []


def fetch_all_confidatasem(company, user, search_query=None):
    try:
        with connection.cursor() as cursor:
            company_id = int(company.id)
            user_id = int(user.id)
            
            if search_query is None:
                search_query = ""

            # Debug: Imprimir los valores que se están pasando al procedimiento almacenado
            print(f"Ejecutando procedimiento almacenado con CompanyId={company_id}, UserId={user_id}, SearchQuery={search_query}")

            # Llamada al procedimiento almacenado con el parámetro correctamente formateado
            cursor.execute(
                "EXEC [dbo].[ListConfigDataSeM] @CompanyId=%s, @UserId=%s, @SearchQuery=%s",
                [company_id, user_id, search_query],
            )

            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

            result = [dict(zip(columns, row)) for row in rows]
            print("Resultado de la consulta:", result)  # Debug: Imprimir el resultado de la consulta
            return result
    except DatabaseError as e:
        print("Error de base de datos:", e)
        return []
    except Exception as e:
        print("Error al realizar la consulta fetch_all_confidatasem:", e)
        return []