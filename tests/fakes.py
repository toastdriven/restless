class FakeHttpRequest(object):
    def __init__(self, method='GET', body=''):
        self.method = method.upper()
        self.body = body


class FakeHttpResponse(object):
    def __init__(self, body, content_type='text/html'):
        self.body = body
        self.content_type = content_type
        self.status_code = 200


class FakeModel(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
