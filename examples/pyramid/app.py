import time
import redis
from wsgiref.simple_server import make_server
from pyramid.config import Configurator

from restless.pyr import PyramidResource

class UserResource(PyramidResource):
    def __init__(self, *args, **kwargs):
        super(UserResource, self).__init__(*args, **kwargs)
        self.conn = redis.StrictRedis(host='localhost', port=6379, db=0)

    def is_authenticated(self):
        return True

    def make_user_key(self, username):
        return 'user_{0}'.format(username)

    def list(self):
        usernames = self.conn.lrange('users', 0, 100)
        users = []

        for user in usernames:
            users.append(self.conn.hgetall(self.make_user_key(user)))

        return users

    def detail(self, username):
        return self.conn.hgetall(self.make_user_key(username))

    def create(self):
        key = self.make_user_key(self.data['username'])
        self.conn.hmset(
            key,
            {
                'username': self.data['username'],
                'email': self.data['email'],
                'added_on': int(time.time()),
            }
        )
        self.conn.rpush('users', self.data['username'])
        return self.conn.hgetall(key)

if __name__ == '__main__':
    config = Configurator()
    config = UserResource.add_views(config, '/users/')
    app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 8080, app)
    server.serve_forever()
