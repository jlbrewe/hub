# Generated by Django 3.0.6 on 2020-06-12 01:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import imagefield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, help_text='The time the account was created.')),
                ('name', models.SlugField(help_text='Name of the account. Lowercase and no spaces or leading numbers. Will be used in URLS e.g. https://hub.stenci.la/awesome-org', max_length=64, unique=True)),
                ('image', imagefield.fields.ImageField(blank=True, height_field='image_height', help_text='Image for the account.', null=True, upload_to='', width_field='image_width')),
                ('display_name', models.CharField(blank=True, help_text='Name to display in account profile.', max_length=256, null=True)),
                ('location', models.CharField(blank=True, help_text='Location to display in account profile.', max_length=256, null=True)),
                ('website', models.URLField(blank=True, help_text='URL to display in account profile.', null=True)),
                ('email', models.EmailField(blank=True, help_text='Email to display in account profile.', max_length=254, null=True)),
                ('theme', models.TextField(blank=True, help_text='The name of the theme to use as the default when generating content for this account.', null=True)),
                ('hosts', models.TextField(blank=True, help_text='A space separated list of valid hosts for the account. Used for setting Content Security Policy headers when serving content for this account.', null=True)),
                ('image_width', models.PositiveIntegerField(blank=True, editable=False, null=True)),
                ('image_height', models.PositiveIntegerField(blank=True, editable=False, null=True)),
                ('image_ppoi', imagefield.fields.PPOIField(default='0.5x0.5', max_length=20)),
                ('creator', models.ForeignKey(blank=True, help_text='The user who created the account.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='accounts_created', to=settings.AUTH_USER_MODEL)),
                ('user', models.OneToOneField(blank=True, help_text='The user for this account. Only applies to personal accounts.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='personal_account', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AccountUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('MEMBER', 'Member'), ('MANAGER', 'Manager'), ('OWNER', 'Admin')], help_text='Role the user has within the account.', max_length=32)),
                ('account', models.ForeignKey(help_text='Account to which the user belongs.', on_delete=django.db.models.deletion.CASCADE, related_name='users', to='accounts.Account')),
                ('user', models.ForeignKey(help_text='User added to the account.', on_delete=django.db.models.deletion.CASCADE, related_name='accounts', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AccountTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.SlugField(help_text='Name of the team.')),
                ('description', models.TextField(blank=True, help_text='Team description.', null=True)),
                ('account', models.ForeignKey(help_text='Account to which the team belongs.', on_delete=django.db.models.deletion.CASCADE, related_name='teams', to='accounts.Account')),
                ('members', models.ManyToManyField(help_text='Team members.', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='accountuser',
            constraint=models.UniqueConstraint(fields=('account', 'user'), name='accountuser_unique_account_user'),
        ),
        migrations.AddConstraint(
            model_name='accountteam',
            constraint=models.UniqueConstraint(fields=('account', 'name'), name='accountteam_unique_account_name'),
        ),
    ]
