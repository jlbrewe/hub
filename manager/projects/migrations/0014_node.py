# Generated by Django 3.1.2 on 2020-10-05 19:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0013_auto_20200827_2212'),
    ]

    operations = [
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, help_text='When the project was created.')),
                ('app', models.TextField(blank=True, help_text='An identifier for the app that created the node.', null=True)),
                ('host', models.URLField(blank=True, help_text='URL of the host document within which the node was created.', null=True)),
                ('key', models.TextField(db_index=True, help_text='The key to the node')),
                ('json', models.JSONField(help_text='The JSON content of node.')),
                ('creator', models.ForeignKey(blank=True, help_text='User who created the project.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='nodes_created', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(blank=True, help_text='The project this node is associated with.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='nodes', to='projects.project')),
            ],
            options={
                'unique_together': {('project', 'key')},
            },
        ),
    ]
