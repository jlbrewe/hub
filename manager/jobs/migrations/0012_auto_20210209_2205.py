# Generated by Django 3.1.6 on 2021-02-09 22:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0011_auto_20201127_0625'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='method',
            field=models.CharField(choices=[('parallel', 'parallel'), ('series', 'series'), ('chain', 'chain'), ('clean', 'clean'), ('archive', 'archive'), ('zip', 'zip'), ('pull', 'pull'), ('push', 'push'), ('extract', 'extract'), ('decode', 'decode'), ('encode', 'encode'), ('convert', 'convert'), ('pin', 'pin'), ('register', 'register'), ('compile', 'compile'), ('build', 'build'), ('execute', 'execute'), ('session', 'session'), ('sleep', 'sleep')], help_text='The job method.', max_length=32),
        ),
    ]
