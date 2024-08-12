from django.db import connection
from django.db.models.signals import post_migrate
from django.dispatch import receiver

# @receiver(post_migrate)
# def create_schema(sender, **kwargs):
#     if sender.name == 'apps.checkpoints':  # Reemplaza 'your_app_name' por el nombre de tu aplicación
#         with connection.cursor() as cursor:
#             cursor.execute('ALTER SCHEMA PowerBI TRANSFER advanced_analytical')
