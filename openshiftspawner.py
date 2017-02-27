import os
import string
import subprocess

from jupyterhub.spawner import Spawner

import tornado.gen
import tornado.concurrent
import tornado.process

SRC_ROOT = os.environ['WARPDRIVE_SRC_ROOT']

START_COMMAND = os.path.join(SRC_ROOT, 'start-instance.sh')
STOP_COMMAND = os.path.join(SRC_ROOT, 'stop-instance.sh')
POLL_COMMAND = os.path.join(SRC_ROOT, 'poll-instance.sh')

def execute_command(*command, env=None):
    future = tornado.concurrent.Future()

    try:
        process = tornado.process.Subprocess(command, env=env)

    except OSError as error:
        future.set_exception(ValueError(command))
        return future

    def finish(returncode):
        if returncode:
            future.set_exception(ValueError(command))
        else:
            future.set_result(process.stdout)

    process.set_exit_callback(finish)

    return future

class OpenShiftSpawner(Spawner):

    def __init__(self, *args, **kwargs):
        print('OpenShiftSpawner()', args, kwargs)

        super().__init__(*args, **kwargs)

        # Make sure username matches the restrictions for DNS labels.

        safe_chars = set(string.ascii_lowercase + string.digits)
        safe_username = ''.join([s if s in safe_chars else '-'
                for s in self.user.name.lower()])

        hostname = os.environ['HOSTNAME']

        self.service = '-'.join(hostname.split('-')[:-2])
        self.appid = '%-%s' % (service, safe_username)

        print('appid', self.appid)

    def load_state(self, state):
        print('load_state()', state)
        """Restore state of spawner from database.

        Called for each user's spawner after the hub process restarts.
        `state` is a dict that'll contain the value returned by
        `get_state` of the spawner, or {} if the spawner hasn't
        persisted any state yet. Override in subclasses to restore any
        extra state that is needed to track the single-user server for
        that user. Subclasses should call super().

        """

        pass

    def get_state(self):
        print('get_state()')
        """Save state of spawner into database.

        A black box of extra state for custom spawners. The returned
        value of this is passed to `load_state`. Subclasses should call
        `super().get_state()`, augment the state returned from there,
        and return that state.

        Returns
        -------
        state: dict
             a JSONable dict of state

        """

        state = {}
        return state

    @tornado.gen.coroutine
    def start(self):
        print('start()')
        """
        Start the single-user server

        Returns:
          (str, int): the (ip, port) where the Hub can connect to the server.

        """

        print('ENV', self.get_env())

        env = os.environ.copy()

        env['JUPYTERHUB_API_TOKEN'] = self.api_token
        env['JUPYTERHUB_API_URL'] = self.hub.api_url

        env['JUPYTERHUB_SERVICE_PREFIX'] = self.hub.server.base_url
        env['JUPYTERHUB_SERVICE_NAME'] = self.user.server.cookie_name

        env['JUPYTER_NOTEBOOK_PREFIX'] = self.user.server.base_url
        env['JUPYTER_NOTEBOOK_USER'] = self.user.name

        yield execute_command(START_COMMAND, self.service, self.appid, env=env)

        host = self.appid
        port = 8080

        return (host, port)

    @tornado.gen.coroutine
    def stop(self, now=False):
        print('stop()', now)
        """
        Stop the single-user server.

        If `now` is set to `False`, do not wait for the server to stop.
        Otherwise, wait for the server to stop before returning. Must be
        a Tornado coroutine.

        """

        yield execute_command(STOP_COMMAND, self.service, self.appid)

    @tornado.gen.coroutine
    def poll(self):
        """
        Check if the single-user process is running

        Returns:
          None if single-user process is running.
          Integer exit status (0 if unknown), if it is not running.

        State transitions, behavior, and return response:

        - If the Spawner has not been initialized (neither loaded state,
          nor called start), it should behave as if it is not running
          (status=0).

        - If the Spawner has not finished starting, it should behave as if
          it is running (status=None).

        Design assumptions about when `poll` may be called:

        - On Hub launch: `poll` may be called before `start` when state is
          loaded on Hub launch. `poll` should return exit status 0 (unknown)
          if the Spawner has not been initialized via `load_state` or
          `start`.

        - If `.start()` is async: `poll` may be called during any yielded
          portions of the `start` process. `poll` should return None when
          `start` is yielded, indicating that the `start` process has not
          yet completed.

        """

        try:
            yield execute_command(POLL_COMMAND, self.service, self.appid)

        except Exception as e:
            return 0

        return None
