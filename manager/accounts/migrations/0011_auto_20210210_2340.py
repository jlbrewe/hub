# Generated by Django 3.1.6 on 2021-02-10 23:40

from django.db import migrations, models
import imagefield.fields
import manager.storage


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_auto_20210203_2054'),
    ]

    operations = [
        migrations.AddField(
            model_name='accounttier',
            name='session_memory_max',
            field=models.PositiveIntegerField(default=500, help_text='The maximum value that the project session memory field can be set at (MiB).', verbose_name='Maximum session memory'),
        ),
        migrations.AddField(
            model_name='accounttier',
            name='session_timelimit_max',
            field=models.PositiveIntegerField(default=3600, help_text='The maximum value that the project session time limit field can be set at (s).', verbose_name='Maximum session time limit'),
        ),
        migrations.AddField(
            model_name='accounttier',
            name='session_timeout_max',
            field=models.PositiveIntegerField(default=600, help_text='The maximum value that the project session timeout field can be set at (s).', verbose_name='Maximum session inactivity timeout'),
        )
    ]
