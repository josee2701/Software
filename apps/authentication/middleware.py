from django.contrib.auth import logout
from django.contrib.sessions.models import Session
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin


class ExpireSessionOnBrowserCloseMiddleware(MiddlewareMixin):
    """
    Este middleware asegura que la sesión del usuario expire cuando se cierre el navegador.
    """

    def process_response(self, request, response):
        """
        Este método se ejecuta después de que la vista ha sido procesada y antes de que la
        respuesta sea enviada al cliente. Configura la cookie de sesión (sessionid) para que expire
        al cerrar el navegador estableciendo expires=None.
        """
        response.set_cookie("sessionid", request.session.session_key, expires=None)
        return response

class SingleSessionPerUserMiddleware(MiddlewareMixin):
    """
    Este middleware garantiza que un usuario solo pueda tener una sesión activa a la vez.
    """

    def process_request(self, request):
        """
        Este método se ejecuta antes de que la vista sea procesada.
        Si el usuario está autenticado, verifica si tiene una sesión previa activa guardada en la
        tabla loggedinuser. Si existe una sesión previa diferente a la actual, elimina la sesión
        previa y actualiza la sesión activa en la base de datos.
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

class ManejoUsuarioNoExistenteMiddleware(MiddlewareMixin):
    """
    Este middleware maneja las excepciones que ocurren cuando un usuario no existe en la base de
    datos, cerrando la sesión y redirigiendo al usuario a la página de inicio de sesión.
    """

    def process_exception(self, request, exception):
        """
        Este método se ejecuta cuando ocurre una excepción durante el procesamiento de la solicitud.
        Si la excepción es del tipo ObjectDoesNotExist, cierra la sesión (logout(request))
        y redirige al usuario a la página de inicio de sesión (redirect('/login/')).
        """
        if isinstance(exception, ObjectDoesNotExist):
            # Aquí puedes especificar una lógica adicional para determinar si el error
            # proviene específicamente de una operación relacionada con el usuario.
            logout(request)
            return redirect("login")  # Asegúrate de reemplazar 'login' con el nombre correcto de tu vista de login.
