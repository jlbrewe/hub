# Generated by Django 3.1.3 on 2020-11-16 05:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0019_googlesheetssource'),
    ]

    operations = [
        migrations.CreateModel(
            name='GithubRepo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, help_text='The time that this record was created.')),
                ('full_name', models.CharField(help_text='The full name of the repository ie. owner/name', max_length=512)),
                ('image_url', models.URLField(help_text='The URL for an image associated with the repository.')),
                ('permissions', models.JSONField(help_text='A JSON object with permissions that the user has for the repo.')),
                ('user', models.ForeignKey(help_text='The user who has access to the repository.', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
