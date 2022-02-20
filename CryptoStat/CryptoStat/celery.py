from __future__ import absolute_import
import os
from celery import Celery
from CryptoStat.AuthAndStat.models import Info

# this code copied from manage.py
# set the default Django settings module for the 'celery' app.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CryptoStat.settings')

# you change the name here
app = Celery("AuthAndStat")

# read config from Django settings, the CELERY namespace would make celery 
# config keys has `CELERY` prefix
app.config_from_object('django.conf:settings')

# load tasks.py in django apps
app.autodiscover_tasks()


@app.task
def add(x, y):
    return x+y


@app.task
def write_in_database(date, currency, equity):
    if Info.objects.filter(date=date, currency=currency).count() == 0:
        m = Info(date=date, currency=currency, equity=equity)
        m.save()
    else:
        ob = Info.objects.get(date=date, currency=currency)
        ob.equity = equity
