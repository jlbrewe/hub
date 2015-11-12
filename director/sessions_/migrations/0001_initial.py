# -*- coding: utf-8 -*-
# Generated by Django 1.9b1 on 2015-11-12 02:12
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0002_initial_data'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('components', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invitee', models.ForeignKey(help_text='User invited to the session', on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, help_text='When this session was created', null=True)),
                ('token', models.CharField(blank=True, help_text='User token used to sigin from the session', max_length=128, null=True)),
                ('image', models.CharField(blank=True, help_text='Image for this session', max_length=64, null=True)),
                ('command', models.CharField(blank=True, help_text='Image for this session', max_length=64, null=True)),
                ('memory', models.CharField(default='1g', help_text='Memory limit for this session. Format: <number><optional unit>, where unit = b, k, m or g', max_length=8, null=True)),
                ('cpu', models.IntegerField(default=1024, help_text='CPU share for this session. Share out of 1024', null=True)),
                ('uuid', models.CharField(blank=True, help_text='Unique identifier for the session', max_length=128, null=True)),
                ('port', models.CharField(blank=True, help_text='Port number for the session on the worker', max_length=16, null=True)),
                ('status', models.CharField(blank=True, help_text='Current status', max_length=32, null=True)),
                ('started_on_worker', models.DateTimeField(blank=True, help_text='Time that this session started on worker', null=True)),
                ('active', models.NullBooleanField(default=None, help_text='Indicates if the session is active or not.')),
                ('ready', models.NullBooleanField(default=False, help_text='Indicates if the session is ready to be connected to')),
                ('started', models.DateTimeField(blank=True, help_text='Time that this session started', null=True)),
                ('updated', models.DateTimeField(blank=True, help_text='Time that this session had its information last updated', null=True)),
                ('stopped', models.DateTimeField(blank=True, help_text='Time that this session was stopped', null=True)),
                ('account', models.ForeignKey(help_text='Account that this session is linked to. Usually not null.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='accounts.Account')),
                ('component', models.ForeignKey(help_text='Component for this session. Usually not null.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='components.Component')),
                ('user', models.ForeignKey(help_text='User for this session', on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Session',
                'verbose_name_plural': 'Sessions',
            },
        ),
        migrations.CreateModel(
            name='SessionLogs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('captured', models.DateTimeField(auto_now=True, help_text='When this log output was captured', null=True)),
                ('logs', models.TextField(help_text='Log output', null=True)),
                ('session', models.ForeignKey(help_text='Session that this log capture relates to', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='sessions_.Session')),
            ],
            options={
                'verbose_name': 'Session logs',
                'verbose_name_plural': 'Session logs',
            },
        ),
        migrations.CreateModel(
            name='SessionStats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.TextField(help_text='Stats data (usually as JSON) with all stats provided by workerbut not necessarily recorded as a separate field in this table', null=True)),
                ('time', models.DateTimeField(help_text='Time that this information relates to', null=True)),
                ('cpu_user', models.FloatField(help_text='Accumulated user CPU time for the session', null=True)),
                ('cpu_system', models.FloatField(help_text='Accumulated system CPU time for the session', null=True)),
                ('cpu_total', models.FloatField(help_text='Accumulated CPU time for the session', null=True)),
                ('mem_rss', models.FloatField(help_text='Memory held in RAM (RSS: resident set size)', null=True)),
                ('mem_vms', models.FloatField(help_text='Memory held in virtual memory (VMS: virtual memory size)', null=True)),
                ('session', models.ForeignKey(help_text='Session that this information relates to', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stats', to='sessions_.Session')),
            ],
            options={
                'verbose_name': 'Session stats',
                'verbose_name_plural': 'Session stats',
            },
        ),
        migrations.CreateModel(
            name='Worker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(choices=[(b'vbox', b'VirtualBox'), (b'ec2', b'EC2')], help_text='The provider (e.g. Amazon EC2) for the worker', max_length=16, null=True)),
                ('provider_id', models.CharField(blank=True, help_text='The provider specific identifier for the worker. Set when started.', max_length=128, null=True)),
                ('ip', models.CharField(blank=True, help_text='IP address of the worker. Set when started.', max_length=16, null=True)),
                ('port', models.IntegerField(blank=True, default=7320, help_text='Port number of the session agent on the worker. This usually should not be changed from the default value.', null=True)),
                ('active', models.NullBooleanField(default=None, help_text='Indicates if the worker is active or not.')),
                ('started', models.DateTimeField(help_text='Time that the worker was started', null=True)),
                ('updated', models.DateTimeField(help_text='Time that the worker information was last updated', null=True)),
                ('stopped', models.DateTimeField(help_text='Time that the worker was stopped', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='WorkerStats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(null=True)),
                ('sessions', models.IntegerField(null=True)),
                ('users', models.TextField(null=True)),
                ('processes', models.IntegerField(null=True)),
                ('cpu_percent', models.FloatField(null=True)),
                ('cpu_user', models.FloatField(null=True)),
                ('cpu_system', models.FloatField(null=True)),
                ('cpu_idle', models.FloatField(null=True)),
                ('cpu_nice', models.FloatField(null=True)),
                ('cpu_iowait', models.FloatField(null=True)),
                ('cpu_irq', models.FloatField(null=True)),
                ('cpu_softirq', models.FloatField(null=True)),
                ('mem_total', models.FloatField(null=True)),
                ('mem_available', models.FloatField(null=True)),
                ('mem_percent', models.FloatField(null=True)),
                ('mem_used', models.FloatField(null=True)),
                ('mem_free', models.FloatField(null=True)),
                ('mem_active', models.FloatField(null=True)),
                ('mem_inactive', models.FloatField(null=True)),
                ('mem_cached', models.FloatField(null=True)),
                ('swap_total', models.FloatField(null=True)),
                ('swap_used', models.FloatField(null=True)),
                ('swap_free', models.FloatField(null=True)),
                ('swap_percent', models.FloatField(null=True)),
                ('swap_sin', models.FloatField(null=True)),
                ('swap_sout', models.FloatField(null=True)),
                ('disk_use_total', models.FloatField(null=True)),
                ('disk_use_used', models.FloatField(null=True)),
                ('disk_use_free', models.FloatField(null=True)),
                ('disk_use_percent', models.FloatField(null=True)),
                ('disk_io_read_count', models.FloatField(null=True)),
                ('disk_io_write_count', models.FloatField(null=True)),
                ('disk_io_read_bytes', models.FloatField(null=True)),
                ('disk_io_write_bytes', models.FloatField(null=True)),
                ('disk_io_read_time', models.FloatField(null=True)),
                ('disk_io_write_time', models.FloatField(null=True)),
                ('net_io_bytes_sent', models.FloatField(null=True)),
                ('net_io_bytes_recv', models.FloatField(null=True)),
                ('net_io_packets_sent', models.FloatField(null=True)),
                ('net_io_packets_recv', models.FloatField(null=True)),
                ('net_io_errin', models.FloatField(null=True)),
                ('net_io_errout', models.FloatField(null=True)),
                ('net_io_dropin', models.FloatField(null=True)),
                ('net_io_dropout', models.FloatField(null=True)),
                ('worker', models.ForeignKey(help_text='Worker that the information relates to', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stats', to='sessions_.Worker')),
            ],
            options={
                'verbose_name': 'Worker stats',
                'verbose_name_plural': 'Worker stats',
            },
        ),
        migrations.AddField(
            model_name='session',
            name='worker',
            field=models.ForeignKey(blank=True, help_text='Worker that this session is running on', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='sessions_.Worker'),
        ),
        migrations.AddField(
            model_name='invitation',
            name='session',
            field=models.ForeignKey(help_text='Session that this invitation realtes to', on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='sessions_.Session'),
        ),
    ]
