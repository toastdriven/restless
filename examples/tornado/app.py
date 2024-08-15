import tornado.ioloop
from tornado import web, gen
from restless.tnd import TornadoResource

class PetResource(TornadoResource):
    def prepare(self):
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
