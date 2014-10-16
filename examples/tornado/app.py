import tornado.ioloop
from tornado import web, gen
from restless.tnd import TornadoResource


class BaseHandler(web.RequestHandler):

    def prepare(self):
        """ do normal tornado preparation """

    def initialize(self):
        """ do your tornado initialization """

class PetResource(TornadoResource):

    # bind BaseHandler instead of tornado.web.RequestHandler
    _request_handler_base_ = BaseHandler

    def __init__(self):
        self.fake_db = [
            {
                "id": 1,
                "name": "Mitti",
                "type": "dog"
            },
            {
                "id": 2,
                "name": "Gary",
                "type": "cat"
            }
        ]


    @gen.coroutine
    def list(self):
        raise gen.Return(self.fake_db)


routes = [
    (r'/pets', PetResource.as_list()),
    (r'/pets/([^/]+)', PetResource.as_detail())
]

app = web.Application(routes, debug=True)

if __name__ == '__main__':
    app.listen(8001)
    tornado.ioloop.IOLoop.instance().start()

