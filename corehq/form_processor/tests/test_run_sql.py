from __future__ import unicode_literals
from __future__ import absolute_import
from datetime import datetime, timedelta
from io import BytesIO
from pprint import pformat, pprint
from uuid import uuid4

from django.db import connections
from django.test import TransactionTestCase

from corehq.blobs import CODES
from corehq.blobs.models import BlobMeta
from corehq.blobs.tests.util import new_meta, TemporaryFilesystemBlobDB
from corehq.form_processor.management.commands.run_sql import (
    Command,
    get_form_attachment_blob_metas_by_key,
)
from corehq.form_processor.models import (
    DeprecatedXFormAttachmentSQL,
    XFormInstanceSQL,
)
from corehq.sql_db.util import (
    get_db_alias_for_partitioned_doc,
    get_db_aliases_for_partitioned_query,
    new_id_in_same_dbalias,
)


class TestRunSql(TransactionTestCase):
    # this can be removed with form_processor_xformattachmentsql table

    @classmethod
    def setUpClass(cls):
        super(TestRunSql, cls).setUpClass()
        cls.db = TemporaryFilesystemBlobDB()
        for db in get_db_aliases_for_partitioned_query():
            with connections[db].cursor() as cursor:
                cursor.execute("""
                DROP TRIGGER IF EXISTS legacy_xform_attachment_insert_not_allowed
                    ON form_processor_xformattachmentsql;
                """)
        # this test requires a clean slate (no forms or blob metadata)
        cls.delete_all_forms_and_blob_metadata()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        super(TestRunSql, cls).tearDownClass()

        for db in get_db_aliases_for_partitioned_query():
            with connections[db].cursor() as cursor:
                cursor.execute("""
                CREATE TRIGGER legacy_xform_attachment_insert_not_allowed
                    BEFORE INSERT ON form_processor_xformattachmentsql
                    EXECUTE PROCEDURE insert_not_allowed();
                """)

    @classmethod
    def delete_all_forms_and_blob_metadata(cls):
        for db in get_db_aliases_for_partitioned_query():
            with connections[db].cursor() as cursor:
                cursor.execute("""
                DELETE FROM blobs_blobmeta;
                DELETE FROM form_processor_xformattachmentsql;
                DELETE FROM form_processor_xforminstancesql;
                """)

    def _fixture_teardown(self):
        # Normally _fixture_teardown truncates all tables on all databases,
        # which takes a long time. This just cleans up what we created.
        self.delete_all_forms_and_blob_metadata()

    def create_metas(self, action="normal"):
        def attach(meta, form_id, **kw):
            # put metadata into xformattachmentsql table
            db = get_db_alias_for_partitioned_doc(form_id)
            if meta.name == "form.xml":
                XFormInstanceSQL(
                    domain=meta.domain,
                    form_id=form_id,
                    received_on=RECEIVED_ON,
                    xmlns="testing",
                    **kw
                ).save(using=db)
            DeprecatedXFormAttachmentSQL(
                form_id=form_id,
                attachment_id=uuid4().hex,
                blob_id=meta.key,
                blob_bucket="",
                name=meta.name,
                content_length=meta.content_length,
                md5='wrong',
            ).save(using=db)

        def iter_keys(parent_id, name, code):
            args = {
                "parent_id": parent_id,
                "type_code": (CODES.form_xml if "badcode" in action else code),
                "name": name,
                "key": parent_id + "-" + name,
                "content_length": 2,
            }
            if "dup" not in action:
                args["created_on"] = RECEIVED_ON
            meta = new_meta(**args)

            yield parent_id, code, name
            deprecated = "deprecated" in action
            if deprecated:
                form_id = get_new_id(parent_id)
                yield form_id, code, name
            else:
                form_id = parent_id
            attach(meta, form_id, orig_id=(parent_id if deprecated else None))
            meta_count = 1
            if action != "normal":
                meta = self.db.put(BytesIO(b"cx"), meta=meta)
                meta_count += 1
                if "old" in action:
                    assert deprecated, action
                    attach(meta, parent_id, deprecated_form_id=form_id)
                    if "dup" in action:
                        meta_count += 1
                    else:
                        assert "badcode" not in action, action
                        meta.delete()
                if "x3" in action:
                    meta_count += 1
                    third_id = get_new_id(form_id)
                    attach(meta, third_id, deprecated_form_id=form_id)
                    yield third_id, code, name
            db = get_db_alias_for_partitioned_doc(parent_id)
            metas = (
                list(BlobMeta.objects.using(db).filter(key=meta.key)) +
                list(get_form_attachment_blob_metas_by_key(meta.key, db))
            )
            assert len(metas) == meta_count, (metas, action, meta_count)

        def get_new_id(parent_id):
            if parent_id not in deprecated_ids:
                deprecated_ids[parent_id] = new_id_in_same_dbalias(parent_id)
            return deprecated_ids[parent_id]

        deprecated_ids = {}
        keys = set(iter_keys(action, "form.xml", CODES.form_xml))
        keys.update(iter_keys(action, "pic.jpg", CODES.form_attachment))
        return keys

    def get_metas(self, model=BlobMeta):
        metas = []
        for db in get_db_aliases_for_partitioned_query():
            metas.extend(model.objects.using(db).all())
            if model is BlobMeta:
                metas.extend(get_form_attachment_blob_metas_by_key(None, db))
        return metas

    def setUp(self):
        super(TestRunSql, self).setUp()
        self.delete_all_forms_and_blob_metadata()
        self.key_sets = [
            # Normal form, no dups (old metadata).
            self.create_metas(),

            # Form with two sets of blob metadata (old and new metadata).
            self.create_metas("dup"),

            # Form with two sets of blob metadata (old and new metadata).
            self.create_metas("dup-badcode"),

            # Two forms referencing same blob (old and new metadata).
            self.create_metas("deprecated"),

            # Two forms referencing same blob (both old metadata).
            self.create_metas("deprecated-old"),

            # Two forms referencing same blob (two old metadata + one new).
            self.create_metas("dup-deprecated-old"),

            # Three forms referencing same blob (all old metadata).
            self.create_metas("deprecated-old-x3"),
        ]

    def test_simple_move_form_attachments_to_blobmeta(self):
        cmd = Command()
        cmd.handle(
            name="simple_move_form_attachments_to_blobmeta",
            dbname=None,
            chunk_size=100,
            print_rows=False,
            yes=True,
        )

        metas = self.get_metas()
        actual_keys = {get_key(meta) for meta in metas}
        expect_keys = {key for keys in self.key_sets for key in keys}
        # all keys present in blobmeta table
        self.assertEqual(actual_keys, expect_keys,
            "actual keys != expected keys\n" +
            pformat([actual_keys] + list(self.key_sets)))
        # all created_on dates set correctly
        self.assertTrue(all(m.created_on == RECEIVED_ON for m in metas),
            pformat([get_key(m, 1) for m in metas if m.created_on != RECEIVED_ON]))
        # no blobmeta records left in formattachmentsql table
        attachments = self.get_metas(DeprecatedXFormAttachmentSQL)
        self.assertEqual(attachments, [])

    def test_move_form_attachments_to_blobmeta(self):
        pre_metas = self.get_metas()
        pprint({get_key(meta, 1) for meta in pre_metas})

        cmd = Command()
        cmd.handle(
            name="move_form_attachments_to_blobmeta",
            dbname=None,
            # small chunk size to avoid
            # ON CONFLICT DO UPDATE command cannot affect row a second time
            chunk_size=1,
            print_rows=False,
            yes=True,
        )

        # some attachments will not be processed, need to be handled separately
        attachments = self.get_metas(DeprecatedXFormAttachmentSQL)
        self.assertNotEqual(attachments, [])

        metas = self.get_metas()
        actual_keys = {get_key(meta) for meta in metas}
        expect_keys = {key for keys in self.key_sets for key in keys}
        # all keys present in blobmeta table
        self.assertTrue(actual_keys.issubset(expect_keys),
            "actual keys is not a subset of expected keys:\n" +
            pformat([actual_keys] + list(self.key_sets)) +
            "\ndifference:\n" + pformat(expect_keys - actual_keys))
        # some metadata was migrated (maybe not all)
        self.assertGreater(
            len(attachments),
            sum(1 for m in pre_metas if m.id > 0),
            "nothing migrated",
        )

    def test_delete_dup_form_attachments(self):
        cmd = Command()
        cmd.handle(
            name="delete_dup_form_attachments",
            dbname=None,
            chunk_size=100,
            print_rows=False,
            yes=True,
        )

        metas = self.get_metas()
        actual_keys = {get_key(meta) for meta in metas}
        expect_keys = {key for keys in self.key_sets for key in keys}
        # all keys present in blobmeta table
        self.assertEqual(actual_keys, expect_keys,
            "actual keys != expected keys\n" +
            pformat([actual_keys] + list(self.key_sets)) +
            "\ndifference:\n" + pformat(expect_keys - actual_keys))
        # all created_on dates set correctly
        self.assertTrue(all(m.created_on == RECEIVED_ON for m in metas),
            pformat([get_key(m, 1) for m in metas if m.created_on != RECEIVED_ON]))
        # all duplicates should have been deleted
        old_keys = {(m.form_id, m.blob_id)
            for m in self.get_metas(DeprecatedXFormAttachmentSQL)}
        new_keys = {(m.parent_id, m.key) for m in metas if m.id > 0}
        self.assertFalse(old_keys.intersection(new_keys),
            "some duplicate records were not deleted\n" +
            pformat(old_keys.intersection(new_keys)))


# put it back far enough so it's in a different year
RECEIVED_ON = datetime.now() - timedelta(days=400)


def get_key(meta, with_created_on=False):
    key = (meta.parent_id, meta.type_code, meta.name)
    if with_created_on:
        key += meta.created_on.year, meta.id
    return key
