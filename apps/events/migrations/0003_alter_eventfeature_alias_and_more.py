# Generated by Django 4.0.7 on 2024-07-18 15:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_event_modified_by_event_visible'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventfeature',
            name='alias',
            field=models.CharField(max_length=30, verbose_name='Envelope name'),
        ),
        migrations.AlterField(
            model_name='eventfeature',
            name='central_alarm',
            field=models.BooleanField(default=False, verbose_name='Central alarm'),
        ),
    ]
