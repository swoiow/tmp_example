from os import environ

from django.apps import AppConfig

__redis_info__ = environ["REDIS"].split(":")


class AdmConfig(AppConfig):
    name = 'adm'

    rds_host = __redis_info__[0]
    rds_port = __redis_info__[1] if len(__redis_info__) > 1 else 6379
