# Generated by Django 3.0.8 on 2020-07-22 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0006_auto_20200722_0510'),
    ]

    operations = [
        migrations.AddField(
            model_name='snapshot',
            name='path',
            field=models.CharField(help_text="The path of the snapshot's directory within the snapshot storage volume.", max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='snapshot',
            name='zip_name',
            field=models.CharField(help_text="The name of snapshot's Zip file (within the snapshot directory).", max_length=1024, null=True),
        ),
    ]