from __future__ import absolute_import
from pprint import pprint

from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.http import *

from .forms import UserForm, InfoForm
import json
from .models import Info
from CryptoStat.celery import app
import CryptoStat
from openapi_client import configuration, api_client, ApiException
from openapi_client.api import *
from celery.app.control import Control
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import datetime


def index(request):
    data = dict()
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            CryptoStat.settings.TIME_FOR_REFRESH = form.cleaned_data['time_refresh']
            tasks = app.control.inspect()
            actives = tasks.active()
            if actives is not None:
                if len(actives[list(actives.keys())[0]]) != 0:
                    control = Control(app)
                    control.revoke(actives[list(actives.keys())[0]][0]['id'], terminate=True)
            try:
                # Setup configuration instance
                conf = configuration.Configuration()
                # Setup unauthenticated client
                client = api_client.ApiClient(conf)
                publicApi = public_api.PublicApi(client)
                # Authenticate with API credentials
                CryptoStat.settings.USER_ID = form.cleaned_data['user_id']
                CryptoStat.settings.API_KEY = form.cleaned_data['api_key']
                response = publicApi.public_auth_get('client_credentials', '', '', form.cleaned_data['user_id'],
                                                     form.cleaned_data['api_key'], '', '',
                                                     '', scope='session:test wallet:read')
                pprint(response)
                CryptoStat.settings.ACCESS_TOKEN = response['result']['access_token']
                print(CryptoStat.settings)
                try:
                    task = PeriodicTask.objects.get(name='authorize')
                    task.args = json.dumps([CryptoStat.settings.USER_ID, CryptoStat.settings.API_KEY])
                except PeriodicTask.DoesNotExist:
                    try:
                        schedule = IntervalSchedule.objects.get(every=5, period=IntervalSchedule.MINUTES)
                    except IntervalSchedule.DoesNotExist:
                        schedule = IntervalSchedule.objects.create(every=5, period=IntervalSchedule.MINUTES)

                    task = PeriodicTask.objects.create(interval=schedule, name='authorize',
                                                       task='authorize',
                                                       args=json.dumps([CryptoStat.settings.USER_ID,
                                                                        CryptoStat.settings.API_KEY]))

                task.enabled = True  # если задача при первом enable сразу запускается то false
                task.save()

                try:
                    task = PeriodicTask.objects.get(name='write_in_database')
                    task.args = json.dumps([CryptoStat.settings.ACCESS_TOKEN])
                    task.save()
                except PeriodicTask.DoesNotExist:
                    try:
                        schedule = IntervalSchedule.objects.get(every=CryptoStat.settings.TIME_FOR_REFRESH,
                                                                period=IntervalSchedule.SECONDS)
                    except IntervalSchedule.DoesNotExist:
                        schedule = IntervalSchedule.objects.create(every=CryptoStat.settings.TIME_FOR_REFRESH,
                                                                   period=IntervalSchedule.SECONDS)
                    print('Token')
                    print(CryptoStat.settings.ACCESS_TOKEN)
                    task = PeriodicTask.objects.create(interval=schedule, name='write_in_database',
                                                       task='write_in_database',
                                                       args=json.dumps([CryptoStat.settings.ACCESS_TOKEN]))
                    task.enabled = False
                    task.save()
                form = UserForm()
                data['error'] = ''
                return HttpResponseRedirect('/stat')
            except ApiException as ex:
                data['error'] = 'Неверный идентификатор пользователя или API ключ'
        else:
            data['error'] = 'Invalid form'
    else:
        form = UserForm()
        data['error'] = ''
    data['form'] = form
    return render(request, "AuthAndStat/index.html", data)


def stat(request):
    task = PeriodicTask.objects.get(name='authorize')
    if not task.enabled:
        raise PermissionDenied
    if request.method == 'POST':
        start_date = request.POST['Start']
        end_date = request.POST['End']

        rows = Info.objects.filter(date__gte=start_date, date__lte=end_date)

        d1 = datetime.date.fromisoformat(start_date)
        d2 = datetime.date.fromisoformat(end_date)
        delta = (d2-d1).days

        dates = []
        eth = []
        btc = []
        for i in range(0, delta+1):
            dates.append(d1+datetime.timedelta(days=i))
        print(dates)
        print(len(dates))

        is_find = False
        for i in range(len(dates)):
            for j in range(len(rows)):
                if rows[j].date == dates[i]:
                    is_find = True
                    if rows[j].currency == 'ETH':
                        eth.append(float((str(rows[j].equity))))
                    elif rows[j].currency == 'BTC':
                        btc.append(float((str(rows[j].equity))))
            if not is_find:
                eth.append(None)
                btc.append(None)
            is_find = False
        print(len(eth))
        print(len(btc))
        d = {'eth': [], 'btc': []}
        for i in range(len(dates)):
            print(i)
            d['eth'].append({'x': dates[i].isoformat(), 'y': eth[i]})
            d['btc'].append({'x': dates[i].isoformat(), 'y': btc[i]})
        print(d)
        return HttpResponse(json.dumps(d))
    else:
        form = InfoForm()
        task = PeriodicTask.objects.get(name='write_in_database')
        data = dict()
        data['error'] = ''
        data['form'] = form
        data['isRunning'] = task.enabled
        return render(request, "AuthAndStat/stat.html", data)


def get_status(request):
    task = PeriodicTask.objects.get(name='authorize')
    if not task.enabled:
        raise PermissionDenied
    task = PeriodicTask.objects.get(name='write_in_database')
    if request.method == 'POST':
        if task.enabled:
            task.enabled = False
        else:
            task.enabled = True
        task.save()
    return JsonResponse({'isRunning': task.enabled})


def logout(request):
    task = PeriodicTask.objects.get(name='authorize')
    task.enabled = False
    task.save()
    task = PeriodicTask.objects.get(name='write_in_database')
    task.enabled = False
    task.save()
    return redirect('/')


def realtime(request):
    task = PeriodicTask.objects.get(name='authorize')
    if not task.enabled:
        raise PermissionDenied

    task = PeriodicTask.objects.get(name='write_in_database')

    conf_authed = configuration.Configuration()
    conf_authed.access_token = task.args[2:len(task.args)-2:]
    print('Token - ' + task.args[2:len(task.args)-2:])
    # Use retrieved authentication token to setup private endpoint client
    client_authed = api_client.ApiClient(conf_authed)
    privateApi = private_api.PrivateApi(client_authed)
    return JsonResponse({'btc': privateApi.private_get_account_summary_get(currency='BTC')['result']['equity'],
                         'eth': privateApi.private_get_account_summary_get(currency='ETH')['result']['equity']})
