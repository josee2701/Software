from django.conf import settings


def get_paginate_by(request):
    """
    Obtiene el número de elementos a mostrar por página.

    Parámetros:
    - request: La solicitud HTTP recibida.

    Retorna:
    - paginate_by: El número de elementos a mostrar por página.

    Funcionamiento:
    - Obtiene el valor del parámetro 'paginate_by' de la solicitud GET.
    - Si el valor es un número válido, se devuelve ese número.
    - Si el valor no es un número válido, se devuelve el valor por defecto definido en la
    configuración.
    """
    paginate_by = request.GET.get("paginate_by", str(settings.DEFAULT_PAGINATION))
    try:
        return max(int(paginate_by), 1)  # Asegura que el valor mínimo sea 1
    except ValueError:
        return (
            settings.DEFAULT_PAGINATION
        )  # Retorna el valor por defecto en caso de valor inválido
