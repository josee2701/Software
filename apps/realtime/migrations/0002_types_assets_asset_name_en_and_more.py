# Generated by Django 4.0.7 on 2024-08-08 14:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('realtime', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='types_assets',
            name='asset_name_en',
            field=models.CharField(max_length=200, null=True, verbose_name='asset_name'),
        ),
        migrations.AddField(
            model_name='types_assets',
            name='asset_name_es',
            field=models.CharField(max_length=200, null=True, verbose_name='asset_name'),
        ),
        migrations.AddField(
            model_name='types_assets',
            name='asset_name_it',
            field=models.CharField(max_length=200, null=True, verbose_name='asset_name'),
        ),
    ]
