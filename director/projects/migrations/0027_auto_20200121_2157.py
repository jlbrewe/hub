# Generated by Django 2.2.7 on 2020-01-21 21:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0026_auto_20200121_2132'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='project',
            unique_together={('name', 'account')},
        ),
        migrations.RemoveField(
            model_name='project',
            name='slug',
        ),
    ]