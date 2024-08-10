"""
Módulo que define las señales que escuchará la aplicación.

Para una referencia completa sobre django.signals, consulte
https://docs.djangoproject.com/en/4.1/topics/signals/
https://docs.djangoproject.com/en/4.1/ref/contrib/auth/#topics-auth-signals
"""

from django.contrib.auth import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import LoggedInUser


@receiver(user_logged_in)
def on_user_logged_in(sender, **kwargs):
    """
    Señal que se dispara cada vez que un usuario se conecta: guarda el `id` del usuario y la clave
    de la sesión en la tabla `loggedinuser`.
    """
    LoggedInUser.objects.get_or_create(user=kwargs.get("user"))


@receiver(user_logged_out)
def on_user_logged_out(sender, **kwargs):
    """
    Señal que se dispara cada vez que un usuario se desconecta: elimina el `id` del usuario y la
    clave de la sesión de la tabla `loggedinuser`.
    """
    LoggedInUser.objects.filter(user=kwargs.get("user")).delete()
