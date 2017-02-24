# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from corehq.sql_db.operations import noop_migration


class Migration(migrations.Migration):

    dependencies = [
        ('sql_proxy_accessors', '0007_ledger_accessors'),
    ]

    operations = [
        noop_migration()
    ]
