# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-03-12 10:52
from __future__ import unicode_literals
from __future__ import absolute_import

from django.db import migrations

from corehq.sql_db.operations import RawSQLMigration
from custom.icds_reports.utils.migrations import get_view_migrations


migrator = RawSQLMigration(('custom', 'icds_reports', 'migrations', 'sql_templates', 'database_views'))


class Migration(migrations.Migration):

    dependencies = [
        ('icds_reports', '0105_aww_incentive_report_monthly'),
    ]

    operations = [
        migrator.get_migration('service_delivery_monthly.sql'),
    ]
