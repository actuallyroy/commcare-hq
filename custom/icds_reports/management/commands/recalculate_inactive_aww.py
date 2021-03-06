from __future__ import absolute_import, print_function

from __future__ import unicode_literals
import datetime

from django.core.management.base import BaseCommand

from custom.icds_reports.models import AggregateInactiveAWW


class Command(BaseCommand):
    def handle(self, *args, **options):
        start_date = datetime.date(2017, 3, 1)
        AggregateInactiveAWW.aggregate(start_date)
