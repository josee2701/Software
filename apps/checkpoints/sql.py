from django.db import DatabaseError, connection


def get_drivers_list(user_company_id):
    try:
        with connection.cursor() as cursor:
            # Consulta que selecciona todos los conductores por compañía y sus proveedores
            cursor.execute(
                "EXEC [dbo].[ListCheckpointsDrivers] @CompanyId=%s", [user_company_id]
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
        print("error al realizar la consulta get_drivers_list:", e)
        return None
    
def getCompanyScoresByCompanyAndUser(company_id, user_id):
    try:
        with connection.cursor() as cursor:
            # Consulta que selecciona todas las compañias por compañía y sus proveedores
            cursor.execute("EXEC [dbo].[ListCompanyScoresByCompanyAndUser] @CompanyId=%s, @UserId=%s", [company_id, user_id])
            rows = cursor.fetchall()

            # Usar cursor.description para obtener los nombres de las columnas
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
            
    except DatabaseError as e:
        # Manejar el error de base de datos aquí
        print("Error de base de datos:", e)
        return None
    
    except Exception as e:
        print("error al realizar la consulta ListCompanyScoresByCompanyAndUser:", e)
        return None