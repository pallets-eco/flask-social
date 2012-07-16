

class Provider(object):
    def __init__(self, remote_app, connection_factory,
                 login_handler, connect_handler):
        self.remote_app = remote_app
        self.connection_factory = connection_factory
        self.login_handler = login_handler
        self.connect_handler = connect_handler

    def get_connection(self, *args, **kwargs):
        return self.connection_factory(*args, **kwargs)

    def login_handler(self, *args, **kwargs):
        return self.login_handler(*args, **kwargs)

    def connect_handler(self, *args, **kwargs):
        return self.connect_handler(*args, **kwargs)

    def tokengetter(self, *args, **kwargs):
        return self.remote_app.tokengetter(*args, **kwargs)

    def authorized_handler(self, *args, **kwargs):
        return self.remote_app.authorized_handler(*args, **kwargs)

    def authorize(self, *args, **kwargs):
        return self.remote_app.authorize(*args, **kwargs)

    def __str__(self):
        return '<Provider name=%s>' % self.remote_app.name
