from __future__ import absolute_import
from __future__ import unicode_literals

from datetime import datetime

from django.utils.translation import ugettext as _

from corehq.apps.userreports.columns import get_expanded_column_config
from corehq.apps.userreports.exceptions import UserReportsError
from corehq.apps.userreports.models import get_report_config
from corehq.toggles import INCLUDE_METADATA_IN_UCR_EXCEL_EXPORTS
from corehq.util.timezones.utils import get_timezone_for_domain


def get_expanded_columns(column_configs, data_source_config):
    return {
        column_config.column_id: [
            sql_col.slug for sql_col in get_expanded_column_config(
                data_source_config, column_config, 'en'
            ).columns
        ]
        for column_config in column_configs
        if column_config.type == 'expanded'
    }


def has_location_filter(view_fn, *args, **kwargs):
    """check that the report has at least one location based filter or
    location choice provider filter
    """
    report, _ = get_report_config(config_id=kwargs.get('subreport_slug'), domain=kwargs.get('domain'))
    return any(
        getattr(getattr(filter_, 'choice_provider', None), 'location_safe', False) or
        getattr(filter_, 'location_filter', False)
        for filter_ in report.ui_filters
    )


class ReportExport(object):

    def __init__(self, domain, title, report_config, lang, filter_values):
        self.domain = domain
        self.title = title
        self.report_config = report_config
        self.lang = lang
        self.filter_values = filter_values

    @property
    def data_source(self):
        # The datasource needs to be built again as the ConfigurableReportDataSource object cannot be pickled
        from corehq.apps.userreports.reports.data_source import ConfigurableReportDataSource
        data_source = ConfigurableReportDataSource.from_spec(self.report_config, include_prefilters=True)
        data_source.lang = self.lang
        return data_source

    def get_table(self):
        try:
            data = self.data_source
            data.set_filter_values(self.filter_values)
            data.set_order_by([(o['field'], o['order']) for o in self.report_config.sort_expression])
        except UserReportsError as e:
            return self.render_json_response({
                'error': e,
            })

        raw_rows = list(data.get_data())

        headers = [
            column.header
            for column in self.data_source.inner_columns if column.data_tables_column.visible
        ]

        column_id_to_expanded_column_ids = get_expanded_columns(data.top_level_columns, data.config)
        column_ids = []
        for column in self.report_config.report_columns:
            if column.visible:
                column_ids.extend(column_id_to_expanded_column_ids.get(column.column_id, [column.column_id]))

        rows = [[raw_row[column_id] for column_id in column_ids] for raw_row in raw_rows]
        total_rows = [data.get_total_row()] if data.has_total_row else []

        export_table = [
            [
                self.title,
                [headers] + rows + total_rows
            ]
        ]

        if INCLUDE_METADATA_IN_UCR_EXCEL_EXPORTS.enabled(self.domain):
            time_zone = get_timezone_for_domain(self.domain)
            export_table.append([
                'metadata',
                [
                    [_('Report Name'), self.title],
                    [_('Generated On'), datetime.now(time_zone).strftime('%Y-%m-%d %H:%M')],
                ] + list(self._get_filter_values())
            ])

        return export_table
