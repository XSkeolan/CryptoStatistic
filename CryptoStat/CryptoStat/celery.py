from __future__ import absolute_import
import os
import pickle
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CryptoStat.settings')
from celery import Celery

from pprint import pprint

# from AuthAndStat.models import Info
from datetime import date
from openapi_client import ApiException, configuration, api_client
import openapi_client.api.private_api as private_api

# this code copied from manage.py
# set the default Django settings module for the 'celery' app.


# you change the name here
app = Celery("AuthAndStat")

# read config from Django settings, the CELERY namespace would make celery
# config keys has `CELERY` prefix
app.config_from_object('django.conf:settings', namespace='CELERY')
# app.conf.beat_schedule = {
#     'add-every-30-seconds': {
#         'task': 'write_in_database',
#         'schedule': 5.0,
#     },
# }
app.conf.timezone = 'UTC'
# load tasks.py in django apps
app.autodiscover_tasks()



