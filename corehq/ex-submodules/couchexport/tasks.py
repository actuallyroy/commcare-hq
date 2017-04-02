from celery.utils.log import get_task_logger
from unidecode import unidecode
from celery.task import task
import zipfile
from couchexport.files import Temp
from couchexport.models import Format, ExportSchema, GroupExportConfiguration
import tempfile
import os

from soil import DownloadBase
from soil.util import expose_cached_download
from couchexport.export import SchemaMismatchException, ExportConfiguration

logging = get_task_logger(__name__)


@task
def export_async(custom_export, download_id, format=None, filename=None, **kwargs):
    try:
        export_files = custom_export.get_export_files(format=format, process=export_async, **kwargs)
    except SchemaMismatchException as e:
        # fire off a delayed force update to prevent this from happening again
        rebuild_schemas.delay(custom_export.index)
        expiry = 10*60*60
        expose_cached_download(
            "Sorry, the export failed for %s, please try again later" % custom_export._id,
            expiry,
            None,
            content_disposition="",
            mimetype="text/html",
            download_id=download_id
        ).save(expiry)
    else:
        if export_files:
            if export_files.format is not None:
                format = export_files.format
            if not filename:
                filename = custom_export.name
            return cache_file_to_be_served(export_files.file, export_files.checkpoint, download_id, format, filename)
        else:
            return cache_file_to_be_served(None, None, download_id, format, filename)


@task
def rebuild_schemas(index):
    """
    Resets the schema for all checkpoints to the latest version based off the
    current document structure. Returns the number of checkpoints updated.
    """
    db = ExportSchema.get_db()
    all_checkpoints = ExportSchema.get_all_checkpoints(index)
    config = ExportConfiguration(db, index, disable_checkpoints=True)
    latest = config.create_new_checkpoint()
    counter = 0
    for cp in all_checkpoints:
        cp.schema = latest.schema
        cp.save()
        counter += 1
    return counter


@task
def bulk_export_async(bulk_export_helper, download_id,
                      filename="bulk_export", expiry=10*60*60, domain=None):

    total = sum([len(file.export_objects) for file in bulk_export_helper.bulk_files]) + 1

    def _update_progress(progress):
        DownloadBase.set_progress(bulk_export_async, progress, total)

    _update_progress(1)  # give the user some feedback that something is happening

    if bulk_export_helper.zip_export:
        filename = "%s_%s" % (domain, filename) if domain else filename
        _, path = tempfile.mkstemp()
        os.close(_)
        zf = zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED)
        try:
            for i, file in enumerate(bulk_export_helper.bulk_files):
                try:
                    bulk = Temp(file.generate_bulk_file(update_progress=_update_progress))
                    zf.write(bulk.path, "%s/%s" % (filename, file.filename))
                except Exception as e:
                    logging.exception("FAILED to add file to bulk export archive. %s" % e)
        finally:
            zf.close()

        try:
            return cache_file_to_be_served(
                tmp=Temp(path),
                checkpoint=bulk_export_helper,
                download_id=download_id,
                filename=filename,
                format='zip',
                expiry=expiry
            )
        finally:
            try:
                os.remove(path)
            except OSError as e:
                # the file has already been removed
                pass

    else:
        export_object = bulk_export_helper.bulk_files[0]
        return cache_file_to_be_served(
            tmp=Temp(export_object.generate_bulk_file(update_progress=_update_progress)),
            checkpoint=bulk_export_helper,
            download_id=download_id,
            filename=export_object.filename,
            format=export_object.format,
            expiry=expiry
        )


def escape_quotes(s):
    return s.replace(r'"', r'\"')


def cache_file_to_be_served(tmp, checkpoint, download_id, format=None, filename=None, expiry=10*60*60):
    """
    tmp can be either either a path to a tempfile or a StringIO
    (the APIs for tempfiles vs StringIO are unfortunately... not similar)
    """
    if checkpoint:
        format = Format.from_format(format)
        try:
            filename = unidecode(filename)
        except Exception:
            pass

        escaped_filename = escape_quotes('%s.%s' % (filename, format.extension))

        payload = tmp.payload
        expose_cached_download(payload, expiry, ".{}".format(format.extension),
                        mimetype=format.mimetype,
                        content_disposition='attachment; filename="%s"' % escaped_filename,
                        extras={'X-CommCareHQ-Export-Token': checkpoint.get_id},
                        download_id=download_id)
        tmp.delete()
    else:
        # this just gives you a link saying there wasn't anything there
        expose_cached_download("Sorry, there wasn't any data.", expiry, None,
                        content_disposition="",
                        mimetype="text/html",
                        download_id=download_id).save(expiry)
