import asyncio
import json
import random
import time
from pprint import pprint

from AuthAndStat.models import Info
from datetime import date, datetime, timedelta
from openapi_client import ApiException, configuration, api_client
import openapi_client.api.private_api as private_api
import openapi_client.api.public_api as public_api
from django_celery_beat.models import PeriodicTask

import CryptoStat
from CryptoStat.celery import app


@app.task(name='write_in_database')
def write_in_database(access_token):
    date_write = date.today()
    currency = 'BTC'
    print('begin')
    try:
        print("in try")
        conf_authed = configuration.Configuration()
        conf_authed.access_token = access_token
        # Use retrieved authentication token to setup private endpoint client
        client_authed = api_client.ApiClient(conf_authed)
        privateApi = private_api.PrivateApi(client_authed)

        equity = privateApi.private_get_account_summary_get(currency=currency)['result']['equity']
        if Info.objects.filter(date=date_write, currency=currency).count() == 0:
            print('filtered by date BTC = 0')
            m = Info(date=date_write, currency=currency, equity=equity)
            m.save()
        else:
            print('filtered by date BTC != 0')
            ob = Info.objects.get(date=date_write, currency=currency)
            ob.equity = equity
            ob.save()
        print(equity)
        currency = 'ETH'
        equity = privateApi.private_get_account_summary_get(currency=currency)['result']['equity']
        if Info.objects.filter(date=date_write, currency=currency).count() == 0:
            print('filtered by date ETH = 0')
            m = Info(date=date_write, currency=currency, equity=equity)
            m.save()
        else:
            print('filtered by date ETH != 0')
            # if random.randint(1, 15) == 13:
            #     raise ApiException(302, 'Bad Request')
            ob = Info.objects.get(date=date_write, currency=currency)
            ob.equity = equity
            ob.save()
        print(equity)
    except ApiException as e:
        pprint('Api Error - ' + e.reason)
        if e.reason == 'Unauthorized' or e.reason == 'Bad Request':
            task = PeriodicTask.objects.get(name='authorize')
            print(task)
            task_db = PeriodicTask.objects.get(name='write_in_database')
            task.start_time = datetime.utcnow() + timedelta(0, 10)
            # попробовать поменять start time. Осталось только авторизация
            task.enabled = True
            task.save()

            task_db.enabled = False
            task_db.save()


@app.task(name='authorize')
def authorize(user_id, secret_key):
    print(user_id)
    print(secret_key)
    try:
        # Setup configuration instance
        conf = configuration.Configuration()
        # Setup unauthenticated client
        client = api_client.ApiClient(conf)
        publicApi = public_api.PublicApi(client)
        # Authenticate with API credentials
        response = publicApi.public_auth_get('client_credentials', '', '', user_id,
                                             secret_key, '', '',
                                             '', scope='session:test wallet:read')
        pprint(response)
        task = PeriodicTask.objects.get(name='write_in_database')
        task.args = json.dumps([response['result']['access_token']])
        task.enabled = True
        task.save()
    except ApiException as ex:
        print('authorize error - ' + ex.reason)
