from django.test import SimpleTestCase
from django.test.utils import override_settings

from ..config import PartitionConfig
from ..exceptions import PartitionValidationError

TEST_PARTITION_CONFIG = {
    'shards': {
        'default': [0, 1],
        'proxy': [2, 3],
    },
    'groups': {
        'main': ['default'],
        'proxy': ['proxy'],
        'form_processing': ['db1', 'db2'],
    }
}

INVALID_SHARD_RANGE = {
    'shards': {
        'default': [0, 2],
        'proxy': [1, 4],
    },
    'groups': {
        'main': ['default'],
        'proxy': ['proxy'],
        'form_processing': ['db1', 'db2'],
    }
}

db_dict = {'NAME': 'commcarehq', 'USER': 'commcarehq', 'HOST': 'hqdb0', 'PORT': 5432}
TEST_DATABASES = {
    'default': db_dict,
    'proxy': db_dict,
    'db1': db_dict,
    'db2': db_dict,
}


@override_settings(PARTITION_DATABASE_CONFIG=TEST_PARTITION_CONFIG)
@override_settings(DATABASES=TEST_DATABASES)
class TestPartitionConfig(SimpleTestCase):

    def test_dbs_by_group(self):
        config = PartitionConfig()
        dbs = config.get_form_processing_dbs()
        self.assertIn('db1', dbs)
        self.assertIn('db2', dbs)

    def test_shard_mapping(self):
        config = PartitionConfig()
        mapping = config.shard_mapping()
        self.assertEquals(mapping, {
            0: 'default',
            1: 'default',
            2: 'proxy',
            3: 'proxy',
        })

    @override_settings(PARTITION_DATABASE_CONFIG=INVALID_SHARD_RANGE)
    def test_invalid_shard_range(self):
        with self.assertRaises(PartitionValidationError):
            PartitionConfig()
