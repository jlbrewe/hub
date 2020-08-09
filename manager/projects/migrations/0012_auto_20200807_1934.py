# Generated by Django 3.0.8 on 2020-08-07 19:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0011_auto_20200806_0605'),
    ]

    operations = [
        migrations.CreateModel(
            name='FileDownloads',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.CharField(db_index=True, help_text='The calendar month, in YYYY-MM format, that these download metrics relate to.', max_length=7)),
                ('count', models.PositiveIntegerField(help_text='The number of downloads for the file for the month.')),
                ('file', models.ForeignKey(help_text='The file that these download metrics relate to.', on_delete=django.db.models.deletion.CASCADE, related_name='downloads', to='projects.File')),
            ],
        ),
        migrations.AddConstraint(
            model_name='filedownloads',
            constraint=models.UniqueConstraint(fields=('file', 'month'), name='filedownloads_unique_file_month'),
        ),
    ]