# Generated by Django 2.0.7 on 2018-07-21 05:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('editors', '0001_initial'),
        ('checkouts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='checkout',
            name='editor',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='checkout', to='editors.Editor'),
        ),
    ]
