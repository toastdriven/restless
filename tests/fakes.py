
class FakeHttpRequest:
    def __init__(self, method='GET', body='', **kwargs):
        self.method = method.upper()
        self.body = body.encode('utf-8')
        if self.method == 'GET':
            self.GET = kwargs.get('get_request', {})


class FakeHttpResponse:
    def __init__(self, body, content_type='text/html'):
        self.body = body
        self.content_type = content_type
        self.status_code = 200


class FakeModel:
    def __init_x_(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
