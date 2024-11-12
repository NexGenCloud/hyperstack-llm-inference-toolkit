CONF_SCHEMA = {
    '$schema': 'https://json-schema.org/draft/2020-12/schema',
    'type': 'object',
    'properties': {
        'git': {
             '$ref': '#/$defs/git'
        },
        'hyperstack_api_key': {
            'type': 'string'
        },
        'proxy_instance': {
            '$ref': '#/$defs/proxy_instance'
        },
        'env': {
            '$ref': '#/$defs/env'
        },
        'inference_engine_vms': {
            'type': 'array',
            'items': {
                '$ref': '#/$defs/inference_engine_vm'
            }
        }
    },
    'required': ['git', 'hyperstack_api_key', 'proxy_instance', 'inference_engine_vms'],
    '$defs': {
        'git': {
            'type': 'object',
            'properties': {
                'token': {
                    'type': 'string'
                },
                'url': {
                    'type': 'string'
                },
                'branch': {
                    'type': 'string'
                }
            },
            'required': ['token', 'url', 'branch']
        },
        'env': {
            'type': 'object',
            'properties': {
                'APP_PASSWORD': {
                    'type': 'string'
                },
                'SECRET_KEY': {
                    'type': 'string'
                },
                'SQLALCHEMY_DATABASE_URI': {
                    'type': 'string'
                },
                'MYSQL_ROOT_PASSWORD': {
                    'type': 'string'
                },
                'MYSQL_USER': {
                    'type': 'string'
                },
                'MYSQL_PASSWORD': {
                    'type': 'string'
                },
                'MYSQL_DATABASE': {
                    'type': 'string'
                },
                'CELERY_BROKER_URL': {
                    'type': 'string'
                },
                'CELERY_RESULT_BACKEND': {
                    'type': 'string'
                },
                'HYPERSTACK_API_KEY': {
                    'type': 'string'
                },
                'S3_BUCKET_NAME': {
                    'type': 'string'
                },
                'S3_ENDPOINT_URL': {
                    'type': 'string'
                },
                'S3_ACCESS_KEY': {
                    'type': 'string'
                },
                'S3_SECRET_KEY': {
                    'type': 'string'
                },
                'DB_BACKUP_SCHEDULE_MIN': {
                    'type': 'string'
                },
                'DB_BACKUP_SCHEDULE_HOUR': {
                    'type': 'string'
                },
                'DB_BACKUP_SCHEDULE_DAY_OF_WEEK': {
                    'type': 'string'
                },
                'DB_BACKUP_SCHEDULE_DAY_OF_MONTH': {
                    'type': 'string'
                },
                'DB_BACKUP_SCHEDULE_MONTH_OF_YEAR': {
                    'type': 'string'
                },
            },
            'required': [
                'APP_PASSWORD',
                'SECRET_KEY',
                'SQLALCHEMY_DATABASE_URI',
                'CELERY_BROKER_URL',
                'CELERY_RESULT_BACKEND',
                'HYPERSTACK_API_KEY',
                'MYSQL_ROOT_PASSWORD',
                'MYSQL_USER',
                'MYSQL_PASSWORD',
                'MYSQL_DATABASE',
                'S3_BUCKET_NAME',
                'S3_ENDPOINT_URL',
                'S3_ACCESS_KEY',
                'S3_SECRET_KEY',
                'DB_BACKUP_SCHEDULE_MIN',
                'DB_BACKUP_SCHEDULE_HOUR',
                'DB_BACKUP_SCHEDULE_DAY_OF_WEEK',
                'DB_BACKUP_SCHEDULE_DAY_OF_MONTH',
                'DB_BACKUP_SCHEDULE_MONTH_OF_YEAR',
            ]
        },
        'proxy_instance': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string'
                },
                'environment_name': {
                    'type': 'string'
                },
                'image_name': {
                    'type': 'string'
                },
                'flavor_name': {
                    'type': 'string'
                },
                'key_name': {
                    'type': 'string'
                },
                'security_rules': {
                    'type': 'array',
                    'items': {
                        '$ref': '#/$defs/security_rule'
                    }
                }
            },
            'required': [
                'name',
                'environment_name',
                'flavor_name',
                'key_name',
                'security_rules',
                'image_name',
            ]
        },
        'inference_engine_vm': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string'
                },
                'environment_name': {
                    'type': 'string'
                },
                'image_name': {
                    'type': 'string'
                },
                'flavor_name': {
                    'type': 'string'
                },
                'model_name': {
                    'type': 'string'
                },
                'key_name': {
                    'type': 'string'
                },
                'run_command': {
                    'type': 'string'
                },
                'endpoint_suffix': {
                    'type': 'string'
                },
                'security_rules': {
                    'type': 'array',
                    'items': {
                        '$ref': '#/$defs/security_rule'
                    }
                },
                'port': {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': 65535
                },
            },
            'required': [
                'name',
                'environment_name',
                'flavor_name',
                'image_name',
                'key_name',
                'run_command',
                'model_name',
                'port',
            ]
        },
        'security_rule': {
            'type': 'object',
            'properties': {
                'direction': {
                    'type': 'string',
                    'enum': ['ingress', 'egress']
                },
                'protocol': {
                    'type': 'string'
                },
                'remote_ip_prefix': {
                    'type': 'string',
                    'pattern': r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'
                },
                'port_range_min': {
                    'type': 'integer',
                    'minimum': 0,
                    'maximum': 65535
                },
                'port_range_max': {
                    'type': 'integer',
                    'minimum': 0,
                    'maximum': 65535
                }
            },
            'required': [
                'direction',
                'protocol',
                'remote_ip_prefix',
                'port_range_min',
                'port_range_max'
            ]
        }
    }
}
