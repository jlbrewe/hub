# Generated by Django 2.0.8 on 2018-09-28 08:18

from django.conf import settings
from django.db import migrations, connection


def remove_duplicate_account_user_roles(apps, schema_editor):
    """
    This migration adds a constraint so that duplicate mappings between `Account` and `User` can not exist. In case
    some already do, remove all but one
    """

    cursor = connection.cursor()
    result = cursor.execute("""
        SELECT COUNT(*) as cnt, MIN(id) as id, account_id, user_id 
        FROM accounts_accountuserrole 
        GROUP BY account_id, user_id
        HAVING COUNT(*) > 1
        """)

    if result:
        result_iterator = result  # for SQLITE
    else:
        result_iterator = cursor  # for Postgres

    for row in result_iterator:
        # since we are still in beta/testing phase for this, it does not matter which of the associations is removed
        delete_cursor = connection.cursor()
        delete_cursor.execute("""
        DELETE FROM accounts_accountuserrole WHERE account_id={} AND user_id={} AND id != {}
        """.format(row[1], row[2], row[3]))
        # quick and dirty SQL variable substitution since we're dealing with just numbers here and different cursors
        # based on the DB engine. SQL is bad, don't do this in real life kids
        delete_cursor.close()

    result_iterator.close()


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0005_auto_20180927_2230'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_account_user_roles),
        migrations.AlterUniqueTogether(
            name='accountuserrole',
            unique_together={('user', 'account')},
        ),
    ]
