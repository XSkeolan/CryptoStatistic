from django.shortcuts import render, redirect
from django.http import *
from .forms import UserForm
import asyncio
import websockets
import json


def index(request):
    data = dict()
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            msg = \
                {
                    "method": "public/auth",
                    "params": {
                        "grant_type": "client_credentials",
                        "client_id": form.cleaned_data['user_id'],
                        "client_secret": form.cleaned_data['api_key']
                    },
                    "jsonrpc": "2.0",
                }

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            future = asyncio.get_event_loop().run_until_complete(call_api(json.dumps(msg)))
            future = json.loads(future)  # string to json
            try:
                result = future['result']
                form = UserForm()
                print(type(result))
                data['error'] = ''
                return HttpResponseRedirect('/stat')
            except KeyError:
                data['error'] = 'Invalid id or API key'

    else:
        form = UserForm()
        data['error'] = ''
    data['form'] = form
    return render(request, "AuthAndStat/index.html", data)


def stat(request):
    return HttpResponse("<h1> Stat </h1>")


def settings(request):
    return HttpResponse("<h1> Settings </h1>")


async def call_api(msg):
    print(msg)
    async with websockets.connect('wss://www.deribit.com/ws/api/v2') as websocket:
        await websocket.send(msg)
        if websocket.open:
            response = await websocket.recv()
            return response
