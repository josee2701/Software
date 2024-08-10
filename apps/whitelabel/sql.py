from django.db import DatabaseError, connection


def fetch_all_process(company):
    with connection.cursor() as cursor:
        # Asegurarse de que 'company' es del tipo correcto, por ejemplo, un entero
        company_id = int(company.id)  # Convertir a entero si es necesario

        # Llamada al procedimiento almacenado con el parámetro correctamente formateado
        cursor.execute("EXEC [dbo].[ListProcessByCompany] @CompanyId=%s", [company_id])

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in rows]


def fetch_all_company(company, user):
    with connection.cursor() as cursor:
        # Asegurarse de que 'company' es del tipo correcto, por ejemplo, un entero
        company_id = int(company.id)  # Convertir a entero si es necesario
        user_id = int(user.id)

        # Llamada al procedimiento almacenado con el parámetro correctamente formateado
        cursor.execute(
            "EXEC [dbo].[ListCompanyByUser] @CompanyId=%s , @UserId=%s",
            [company_id, user_id],
        )

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in rows]


def get_ticket_by_user(user_id):
    try:
        with connection.cursor() as cursor:
            # Consulta que selecciona todos los tickets por compañía y sus proveedores
            cursor.execute("EXEC [dbo].[ListTicketsForUser] @UserId=%s", [user_id])
            rows = cursor.fetchall()
            # Usar cursor.description para obtener los nombres de las columnas
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    except DatabaseError as e:
        # Manejar el error de base de datos aquí
        print("Error de base de datos:", e)
        return None

    except Exception as e:
        print("error al realizar la consulta list_ticket_by_user:", e)
        return None
