#!/usr/bin/env python3

import os
import json
import time

from functools import partial

from tornado.gen import coroutine
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.options import define, options, parse_command_line

cached_admin_users = set()
cached_user_whitelist = set()

@coroutine
def backup_details(url, api_token, interval, backups):
    # Fetch the list of users.

    global cached_admin_users
    global cached_user_whitelist

    auth_header = { 'Authorization': 'token %s' % api_token }
    req = HTTPRequest(url=url + '/users', headers=auth_header)
    client = AsyncHTTPClient()
    resp = yield client.fetch(req)
    users = json.loads(resp.body.decode('utf8', 'replace'))

    admin_users = set()
    user_whitelist = set()

    for user in users:
        if user['admin']:
            admin_users.add(user['name'])
        else:
            user_whitelist.add(user['name'])

    timestamp = time.strftime('%Y-%m-%d-%H-%M-%S', time.gmtime())

    os.makedirs(backups, exist_ok=True)

    if admin_users != cached_admin_users:
        name = 'admin_users-%s.txt' % timestamp
        path = os.path.join(backups, name)
        print('creating backup: %s' % path)
        with open(path, 'w') as fp:
            fp.write('\n'.join(admin_users))
        cached_admin_users = admin_users

    if user_whitelist != cached_user_whitelist:
        name = 'user_whitelist-%s.txt' % timestamp
        path = os.path.join(backups, name)
        print('creating backup: %s' % path)
        with open(path, 'w') as fp:
            fp.write('\n'.join(user_whitelist))
        cached_user_whitelist = user_whitelist

if __name__ == '__main__':
    define('url', default=os.environ.get('JUPYTERHUB_API_URL'),
            help="The JupyterHub API URL")
    define('interval', default=600,
            help="Time (in seconds) between checking for changes.")
    define('backups', default='/tmp',
            help="Directory to save backup files.")

    parse_command_line()

    api_token = os.environ['JUPYTERHUB_API_TOKEN']

    loop = IOLoop.current()

    task = partial(backup_details, url=options.url, api_token=api_token,
            interval=options.interval, backups=options.backups)

    # Schedule the first backup immediately because the period callback
    # doesn't start until the end of the first interval

    loop.add_callback(task)

    # Schedule the periodic backup.

    periodic_callback = PeriodicCallback(task, 1000*options.interval)
    periodic_callback.start()

    try:
        loop.start()
    except KeyboardInterrupt:
        pass
