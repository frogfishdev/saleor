# Generated by Django 3.1.2 on 2021-06-21 19:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('maillist', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='User',
            new_name='MailListParticipant',
        ),
    ]
