# Generated by Django 2.2.12 on 2020-04-09 00:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0039_snapshot_refactor'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='theme',
            field=models.TextField(blank=True, help_text='The name of the theme to use as the default when generating content for this project.', null=True),
        ),
        migrations.AlterField(
            model_name='snapshot',
            name='completed',
            field=models.DateTimeField(blank=True, help_text='The date/time the snapshot was completed; null if the snapshot has not yet started.', null=True),
        ),
        migrations.AlterField(
            model_name='snapshot',
            name='project',
            field=models.ForeignKey(help_text='The project the snapshot belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='snapshots', to='projects.Project'),
        ),
    ]