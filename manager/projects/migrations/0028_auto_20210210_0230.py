# Generated by Django 3.1.6 on 2021-02-10 02:30

from django.db import migrations, models
import manager.storage
import projects.models.sources


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0027_auto_20210203_2054'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='order',
            field=models.PositiveIntegerField(blank=True, help_text='The order that the source should be pulled into the project (allows explicit overwriting of one source by another).', null=True),
        ),
    ]
