from __future__ import absolute_import
import datetime

from django.test import TestCase

from casexml.apps.case.tests.util import delete_all_sync_logs
from casexml.apps.phone.models import SyncLog
from corehq.apps.domain.models import Domain
from corehq.apps.users.models import CommCareUser
from corehq.apps.change_feed import topics
from corehq.apps.change_feed.consumer.feed import change_meta_from_kafka_message
from testapps.test_pillowtop.utils import get_test_kafka_consumer


class SyncLogPillowTest(TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        super(SyncLogPillowTest, cls).setUpClass()

        DOMAIN = "synclog_test"
        cls.domain = Domain(name=DOMAIN)
        cls.domain.save()

        cls.ccuser = CommCareUser(
            domain=DOMAIN,
            username='ccuser',
            location_id=cls.somerville.location_id,
            assigned_location_ids=[cls.somerville.location_id],
            last_login=datetime.datetime.now(),
            date_joined=datetime.datetime.now(),
        )
        cls.ccuser.save()

    @classmethod
    def tearDownClass(cls):
        delete_all_sync_logs()
        cls.ccuser.delete()
        cls.domain.delete()
        super(SyncLogPillowTest, cls).tearDownClass()

    def test_pillow(self):
        consumer = get_test_kafka_consumer(topics.SYNCLOG)

        # make sure user has empty reporting-metadata before a sync
        self.assertEqual(self.ccuser.reporting_metadata.last_syncs, [])
        synclog = SyncLog(domain=self.domain.name, user_id=self.ccuser._id,
                          date=datetime.datetime(2015, 7, 1, 0, 0)),
        synclog.save()
        message = consumer.next()
        change_meta = change_meta_from_kafka_message(message.value)
        self.assertEqual(change_meta.document_id, synclog.synclog_id)
        self.assertEqual(change_meta.domain, self.domain.name, )
