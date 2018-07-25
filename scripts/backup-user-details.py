#!/usr/bin/env python3

import os
import json
import time

from functools import partial

from tornado.gen import coroutine
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.options import define, options, parse_command_line

from kubernetes import config, client
from kubernetes.client.rest import ApiException
from kubernetes.client.models import V1ConfigMap, V1ObjectMeta

service_name = os.environ.get('JUPYTERHUB_SERVICE_NAME')

with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace') as fp:
    namespace = fp.read().strip()

os.environ['KUBERNETES_SERVICE_HOST'] = 'openshift.default.svc.cluster.local'
os.environ['KUBERNETES_SERVICE_PORT'] = '443'

config.load_incluster_config()

corev1api = client.CoreV1Api()

cached_admin_users = None
cached_user_whitelist = None

@coroutine
def backup_details(url, api_token, interval, backups, config_map):
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
            fp.write('\n')

        cached_admin_users = admin_users

        try:
            latest = os.path.join(backups, 'admin_users-latest.txt')
            if os.path.exists(latest):
                os.unlink(latest)
            os.symlink(name, latest)

        except OSError:
            print('ERROR: could not update: admin_users-latest.txt')
            pass

    if user_whitelist != cached_user_whitelist:
        name = 'user_whitelist-%s.txt' % timestamp
        path = os.path.join(backups, name)

        print('creating backup: %s' % path)

        with open(path, 'w') as fp:
            fp.write('\n'.join(user_whitelist))
            fp.write('\n')

        cached_user_whitelist = user_whitelist

        try:
            latest = os.path.join(backups, 'user_whitelist-latest.txt')
            if os.path.exists(latest):
                os.unlink(latest)
            os.symlink(name, latest)

        except OSError:
            print('ERROR: could not update: user_whitelist-latest.txt')
            pass

        if config_map:
            config_map_object = V1ConfigMap()
            config_map_object.kind = "ConfigMap"
            config_map_object.api_version = "v1"

            config_map_object.metadata = V1ObjectMeta(
                name=config_map, labels={'app': service_name})

            config_map_object.data = {
                'admin_users.txt': '\n'.join(admin_users)+'\n',
                'user_whitelist.txt': '\n'.join(user_whitelist)+'\n'
            }

            try:
                corev1api.replace_namespaced_config_map(config_map,
                        namespace, config_map_object)

            except ApiException as e:
                if e.status == 404:
                    try:
                        corev1api.create_namespaced_config_map(
                                namespace, config_map_object)

                    except Exception as e:
                        print('cannot update config map %s: %s' % (config_map, e))

                else:
                    print('cannot update config map %s: %s' % (config_map, e))

            except Exception as e:
                print('cannot update config map %s: %s' % (config_map, e))

if __name__ == '__main__':
    define('url', default=os.environ.get('JUPYTERHUB_API_URL'),
            help="The JupyterHub API URL")
    define('interval', default=300,
            help="Time (in seconds) between checking for changes.")
    define('backups', default='/tmp',
            help="Directory to save backup files.")
    define('config-map', default='',
            help="Name of config map to save backup files.")

    parse_command_line()

    api_token = os.environ['JUPYTERHUB_API_TOKEN']

    loop = IOLoop.current()

    task = partial(backup_details, url=options.url, api_token=api_token,
            interval=options.interval, backups=options.backups,
            config_map=options.config_map)

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
