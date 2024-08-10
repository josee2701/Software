from django.db import DatabaseError, connection


def fetch_all_user(company, user):
    try:
        with connection.cursor() as cursor:
            # Asegurarse de que 'company' es del tipo correcto, por ejemplo, un entero
            company_id = int(company.id)  # Convertir a entero si es necesario

            # Llamada al procedimiento almacenado con el parámetro correctamente formateado
            cursor.execute("EXEC [dbo].[ListUserByCompany] @CompanyId=%s, @UserId=%s", [company_id, user])

            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    except DatabaseError as e:
        # Manejar el error de base de datos aquí
        print("Error de base de datos:", e)
        return None

    except Exception as e:
        print("error al realizar la consulta fetch_all_user:", e)
        return None