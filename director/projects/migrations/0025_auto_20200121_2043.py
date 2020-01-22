# Generated by Django 2.2.7 on 2020-01-21 20:43

from django.db import migrations, IntegrityError
from django.utils.text import slugify


def set_slugs_from_name(apps, schema):
    Project = apps.get_model('projects', 'Project')

    for project in Project.objects.filter(slug__isnull=True) | Project.objects.filter(slug=''):
        if project.name:
            slug = slugify(project.name)
        else:
            slug = 'project-{}'.format(project.pk)

        generated_slug = slug

        slug_number = 2

        while True:
            if slug_number == 100:
                raise RuntimeError(
                    '{} iterations of trying to generate a slug for Project {}'.format(slug_number, project.pk))

            project.slug = slug
            try:
                project.save()
                break
            except IntegrityError:
                slug = '{}-{}'.format(generated_slug, slug_number)
                slug_number += 1


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0024_auto_20200120_0307'),
    ]

    operations = [
        migrations.RunPython(set_slugs_from_name),
    ]