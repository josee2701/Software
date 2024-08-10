from django.db import DatabaseError, connection


def fetch_all_event():
    try:
        with connection.cursor() as cursor:
            # Asegurarse de que 'company' es del tipo correcto, por ejemplo, un entero

            # Llamada al procedimiento almacenado con el parámetro correctamente formateado
            cursor.execute("EXEC [dbo].[ListEnventdByCompany]")

            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    
    except DatabaseError as e:
        # Manejar el error de base de datos aquí
        print("Error de base de datos:", e)
        return []
    
    except Exception as e:
        print("error al realizar la consulta fetch_all_event:", e)
        return []
    

def fetch_all_event_personalized(company, user):
    try:
        with connection.cursor() as cursor:
            # Asegurarse de que 'company' es del tipo correcto, por ejemplo, un entero
            company_id = int(company.id)  # Convertir a entero si es necesario

            # Llamada al procedimiento almacenado con el parámetro correctamente formateado
            cursor.execute("EXEC [dbo].[ListEnventPersonalizedByCompany] @CompanyId=%s, @UserId=%s", [company_id, user])

            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        
    except DatabaseError as e:
        # Manejar el error de base de datos aquí
        print("Error de base de datos:", e)
        return []
    
    except Exception as e:
        print("error al realizar la consulta fetch_all_event_personalized:", e)
        return []
    