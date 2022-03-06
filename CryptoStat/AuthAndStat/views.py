from __future__ import absolute_import
from pprint import pprint

from django.shortcuts import render, redirect
from django.http import *
from openapi_client import ApiException

from .forms import UserForm, InfoForm
import json
from .models import Info
from CryptoStat.celery import app
import CryptoStat
from openapi_client import configuration, api_client
from openapi_client.api import *
from celery.app.control import Control
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import django_celery_beat
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
                try:
                    task = PeriodicTask.objects.get(name='authorize')
                    task.args = json.dumps([CryptoStat.settings.USER_ID,CryptoStat.settings.API_KEY])
                except django_celery_beat.models.PeriodicTask.DoesNotExist:
                    schedule = IntervalSchedule.objects.create(every=10,
                                                               period=IntervalSchedule.MINUTES)
                    task = PeriodicTask.objects.create(interval=schedule,name='authorize',
                                                       task='authorize',
                                                       args=json.dumps([CryptoStat.settings.USER_ID,CryptoStat.settings.API_KEY]))
                    task.enabled = True
                    task.save()
                print(CryptoStat.settings.ACCESS_TOKEN)
                form = UserForm()
                data['error'] = ''
                return HttpResponseRedirect('/stat')
            except ApiException as ex:
                data['error'] = 'Invalid key'
    else:
        form = UserForm()
        data['error'] = ''
    data['form'] = form
    return render(request, "AuthAndStat/index.html", data)


def stat(request):
    if request.method == 'POST':
        start_date = request.POST['Start']
        end_date = request.POST['End']
        rows = Info.objects.filter(date__gte=start_date, date__lte=end_date)
        print(len(rows))
        d1 = datetime.date.fromisoformat(start_date)
        d2 = datetime.date.fromisoformat(end_date)
        delta = (d2-d1).days
        dates = []
        eth = []
        btc = []
        for i in range(0, delta+1):
            dates.append(d1+datetime.timedelta(days=i))
            print(dates[i])
        is_find = False
        for i in range(len(dates)):
            for j in range(len(rows)):
                if rows[j].date == dates[i]:
                    is_find = True
                    if rows[j].currency == 'ETH':
                        eth.append(3)
                    else:
                        btc.append(6)
            if not is_find:
                eth.append(0)
                btc.append(0)
            is_find = False

        d = {'eth': eth, 'btc': btc}
        return HttpResponse(json.dumps(d))
    else:
        form = InfoForm()
        data = dict()
        data['error'] = ''
        data['form'] = form
        tasks = app.control.inspect()
        if tasks.active() is None:
            data['iswork'] = 'Run analysis'
        else:
            data['iswork'] = 'Stop analysis'
        return render(request, "AuthAndStat/stat.html", data)


def getStatus(request):
    if request.method == 'GET':
        try:
            task = PeriodicTask.objects.get(name='write_in_database')
            print(type(task))
            if task.enabled:
                return HttpResponse('Остановить анализ')
            else:
                return HttpResponse('Запустить анализ')
        except django_celery_beat.models.PeriodicTask.DoesNotExist:
            return HttpResponse('Запустить анализ')
    elif request.method == 'POST':
        try:
            task = PeriodicTask.objects.get(name='write_in_database')
            if task.enabled:
                task.enabled = False
                task.save()
                return HttpResponse('Запустить анализ')
            else:
                task.enabled = True
                task.save()
                return HttpResponse('Остановить анализ')
        except django_celery_beat.models.PeriodicTask.DoesNotExist:
            schedule = IntervalSchedule.objects.create(every=CryptoStat.settings.TIME_FOR_REFRESH,
                                                       period=IntervalSchedule.SECONDS)
            task = PeriodicTask.objects.create(interval=schedule, name='write_in_database', task='write_in_database',
                                               args=json.dumps([CryptoStat.settings.ACCESS_TOKEN]))
            task.enabled = True
            task.save()
            return HttpResponse('Остановить анализ')
