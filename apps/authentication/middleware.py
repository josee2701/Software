"""
Middleware (marco de enlaces) que valida los inicios de sesión de los usuarios para dejar solamente
una activa, la más reciente. Depende del módulo de señales que escucha cuando un usuario se
conecta y desconecta, y de la tabla `loggedinuser` que guarda la lista de usuarios en línea y la
clave de sesión en la cual están conectados.

Para más información sobre esta implementación, consulte:
https://gist.github.com/fleepgeek/92b01d3187cf92b4495d71c69ee818df
https://medium.com/scalereal/everything-you-need-to-know-about-middleware-in-django-2a3bd3853cd6

"""

from django.contrib.auth import logout
from django.contrib.sessions.models import Session
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect


class SingleSessionPerUserMiddleware:
    """Se ejecuta una sola vez cuando el servidor inicia."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Código a ejecutar para cada petición antes de llamar a la vista y posteriormente
        al middleware.
        """

        if request.user.is_authenticated:
            # Cuando un usuario se autentifica, verifica en la tabla `loggedinuser` si el usuario
            # está conectado a través de una sesión previa y guarda la clave de esa sesión.
            previous_session = request.user.logged_in_user.session_key

            # Comprueba si la clave de sesión almacenada en la base de datos es diferente de la
            # clave del nuevo inicio de sesión. Si es diferente, elimina la primera clave
            # almacenada y automáticamente desconecta al usuario de la sesión anterior.
            if previous_session is not None:
                try:
                    if previous_session != request.session.session_key:
                        Session.objects.get(session_key=previous_session).delete()
                except Exception:
                    pass

            # Guarda la clave de inicio de sesión actual en la base de datos.
            request.user.logged_in_user.session_key = request.session.session_key
            request.user.logged_in_user.save()

        response = self.get_response(request)

        return response


class ManejoUsuarioNoExistenteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, ObjectDoesNotExist):
            # Aquí puedes especificar una lógica adicional para determinar si el error
            # proviene específicamente de una operación relacionada con el usuario.
            logout(request)
            return redirect(
                "/login/"
            )  # Asegúrate de reemplazar '/login/' con la URL de tu vista de login.
