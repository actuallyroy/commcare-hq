# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-09-11 16:40
from __future__ import unicode_literals
from __future__ import absolute_import
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_interfaces', '0019_remove_old_rule_models'),
    ]

    operations = [
        migrations.AlterField(
            model_name='automaticupdaterule',
            name='migrated',
            field=models.NullBooleanField(),
        ),
    ]