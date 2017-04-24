from corehq.util.elastic import es_index
from corehq.pillows.core import DATE_FORMATS_ARR, DATE_FORMATS_STRING

from pillowtop.es_utils import ElasticsearchIndexInfo

USER_INDEX = es_index("hqusers_2017-04-24")
USER_MAPPING = {'_all': {'analyzer': 'standard'},
 '_meta': {'created': None},
 'date_detection': False,
 'date_formats': DATE_FORMATS_ARR,
 'dynamic': False,
 'properties': {'CURRENT_VERSION': {'type': 'string'},
                'base_doc': {'type': 'string'},
                'created_on': {'format': DATE_FORMATS_STRING,
                               'type': 'date'},
                'date_joined': {'format': DATE_FORMATS_STRING,
                                'type': 'date'},
                'doc_type': {'index': 'not_analyzed', 'type': 'string'},
                'domain': {'fields': {'domain': {'index': 'analyzed',
                                                 'type': 'string'},
                                      'exact': {'index': 'not_analyzed',
                                                'type': 'string'}},
                           'type': 'multi_field'},
                'location_id': {'index': 'not_analyzed', 'type': 'string'},
                'assigned_location_ids': {"type": "string"},
                'domain_membership': {'dynamic': False,
                                      'properties': {'doc_type': {'index': 'not_analyzed',
                                                                  'type': 'string'},
                                                     'domain': {'fields': {'domain': {'index': 'analyzed',
                                                                                      'type': 'string'},
                                                                           'exact': {'index': 'not_analyzed',
                                                                                     'type': 'string'}},
                                                                'type': 'multi_field'},
                                                     'is_admin': {'type': 'boolean'},
                                                     'override_global_tz': {'type': 'boolean'},
                                                     'role_id': {'type': 'string'},
                                                     'timezone': {'type': 'string'},
                                                     'location_id': {'index': 'not_analyzed',
                                                                     'type': 'string'}},
                                      'type': 'object'},
                'domain_memberships': {'dynamic': False,
                                      'properties': {'doc_type': {'index': 'not_analyzed',
                                                                  'type': 'string'},
                                                     'domain': {'fields': {'domain': {'index': 'analyzed',
                                                                                      'type': 'string'},
                                                                           'exact': {'index': 'not_analyzed',
                                                                                     'type': 'string'}},
                                                                'type': 'multi_field'},
                                                     'is_admin': {'type': 'boolean'},
                                                     'override_global_tz': {'type': 'boolean'},
                                                     'role_id': {'type': 'string'},
                                                     'timezone': {'type': 'string'},
                                                     'location_id': {'index': 'not_analyzed',
                                                                     'type': 'string'}},
                                      'type': 'object'},
                'email_opt_out': {'type': 'boolean'},
                'analytics_enabled': {'type': 'boolean'},
                'eulas': {'dynamic': False,
                          'properties': {'date': {'format': DATE_FORMATS_STRING,
                                                  'type': 'date'},
                                         'doc_type': {'index': 'not_analyzed',
                                                      'type': 'string'},
                                         'signed': {'type': 'boolean'},
                                         'type': {'type': 'string'},
                                         'user_id': {'type': 'string'},
                                         'user_ip': {'type': 'string'},
                                         'version': {'type': 'string'}},
                          'type': 'object'},
                'first_name': {'type': 'string'},
                'is_active': {'type': 'boolean'},
                'is_staff': {'type': 'boolean'},
                'is_superuser': {'type': 'boolean'},
                'language': {'type': 'string'},
                'last_login': {'format': DATE_FORMATS_STRING,
                               'type': 'date'},
                'last_name': {'type': 'string'},
                'password': {'type': 'string'},
                'registering_device_id': {'type': 'string'},
                'reporting_metadata': {'dynamic': False,
                                       'properties': {
                                           'last_submissions': {
                                               'dynamic': False,
                                               'properties': {
                                                    'submission_date': {'format': DATE_FORMATS_STRING,
                                                                        'type': 'date'},
                                                    'app_id': {'type': 'string'},
                                                    'build_id': {'type': 'string'},
                                                    'device_id': {'type': 'string'},
                                                    'build_version': {'type': 'integer'},
                                                    'commcare_version': {'type': 'string'},
                                               },
                                               'type': 'object'
                                           }
                                       },
                                       'type': 'object'},
                'status': {'type': 'string'},
                'user_data': {'type': 'object', 'enabled': False},
                'base_username': {'fields': {'base_username': {'index': 'analyzed',
                                                               'type': 'string'},
                                             'exact': {'index': 'not_analyzed',
                                                       'type': 'string'}},
                                 'type': 'multi_field'},
                'username': {'fields': {'exact': {'include_in_all': False,
                                                  'index': 'not_analyzed',
                                                  'type': 'string'},
                                        'username': {'analyzer': 'standard',
                                                     'index': 'analyzed',
                                                     'type': 'string'}},
                             'type': 'multi_field'},
                '__group_ids': {'type': 'string'},
                '__group_names': {'fields': {'__group_names': { 'index': 'analyzed',
                                                                'type': 'string'},
                                             'exact': {'index': 'not_analyzed',
                                                                'type': 'string'}},
                                  'type': 'multi_field'}}}

USER_INDEX_INFO = ElasticsearchIndexInfo(
    index=USER_INDEX,
    alias='hqusers',
    type='user',
    mapping=USER_MAPPING,
)
