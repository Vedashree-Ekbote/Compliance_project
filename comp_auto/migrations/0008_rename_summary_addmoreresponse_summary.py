# Generated by Django 4.1.7 on 2023-11-21 09:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comp_auto', '0007_addmoreresponse'),
    ]

    operations = [
        migrations.RenameField(
            model_name='addmoreresponse',
            old_name='summary',
            new_name='Summary',
        ),
    ]
