from tornado import web, gen
from .constants import OK
from .resources import Resource
from .exceptions import MethodNotImplemented, Unauthorized

import weakref
import inspect


try:
    from tornado.concurrent import is_future
except ImportError:
    is_future = None

if is_future is None:
    """
    Please refer to tornado.concurrent module(newer than 4.0)
    for implementation of this function.
    """
    try:
        from concurrent import futures
    except ImportError:
        futures = None

    from tornado.concurrent import Future

    if futures is None:
        FUTURES = Future
    else:
        FUTURES = (Future, futures.Future)

    is_future = lambda x: isinstance(x, FUTURES)


@gen.coroutine
def _method(self, *args, **kwargs):
    """
    the body of those http-methods used in tornado.web.RequestHandler
    """
    yield self.resource_handler.handle(self.__resource_view_type__, *args, **kwargs)


class _WrappedRequestHandler(web.RequestHandler):
    """
    A wrapper class based on tornado.web.RequestHandler
    to bridge restless and tornado
    """
    def __init__(self, *args, **kwargs):
        super(_WrappedRequestHandler, self).__init__(*args, **kwargs)

        # create a resource instance based on the registered class
        # and init-parameters
        self.resource_handler = self.__class__.__resource_cls__(
            *self.__resource_args__, **self.__resource_kwargs__
        )

        self.resource_handler.request = self.request
        self.resource_handler.application = self.application
        self.resource_handler.ref_rh = weakref.proxy(self) # avoid circular reference between


class TornadoResource(Resource):
    """
    A Tornado-specific ``Resource`` subclass.

    Doesn't require any special configuration, but helps when working in a
    Tornado environment.

    But don't return future from those methods, the Preparer in restless
    are not aware of futre.
    """
    @classmethod
    def as_view(cls, view_type, *init_args, **init_kwargs):
        """
        Return a subclass of tornado.web.RequestHandler and
        apply required setting.
        """
        global _method

        new_cls = type(
            cls.__name__ + '_' +  _WrappedRequestHandler.__name__,
            (_WrappedRequestHandler,),
            dict(
                __resource_cls__=cls,
                __resource_args__=init_args,
                __resource_kwargs__=init_kwargs,
                __resource_view_type__=view_type)
        )

        """
        Add required http-methods to the newly created class
        We need to scan through MRO to find what functions users declared,
        and then add corresponding http-methods used by Tornado.
        """
        bases = inspect.getmro(cls)
        bases = bases[0:bases.index(Resource)-1]
        for k, v in cls.http_methods[view_type].items():
            if any(v in base_cls.__dict__ for base_cls in bases):
                setattr(new_cls, k.lower(), _method)

        return new_cls

    def request_method(self):
        return self.request.method

    def request_body(self):
        return self.request.body 

    def build_response(self, data, status=200):
        self.ref_rh.set_header("Content-Type", "application/json; charset=UTF-8")

        self.ref_rh.set_status(status)
        self.ref_rh.finish(data)

    def is_debug(self):
        return self.application.settings['debug']

    @gen.coroutine
    def handle(self, endpoint, *args, **kwargs):
        """
        almost identical to Resource.handle, except
        the way we handle the return value of view_method.
        """
        method = self.request_method()

        try:
            if not method in self.http_methods.get(endpoint, {}):
                raise MethodNotImplemented(
                    "Unsupported method '{0}' for {1} endpoint.".format(
                        method,
                        endpoint
                    )
                )

            if not self.is_authenticated():
                raise Unauthorized()

            self.data = self.deserialize(method, endpoint, self.request_body())
            view_method = getattr(self, self.http_methods[endpoint][method])
            data = view_method(*args, **kwargs)
            if is_future(data):
                # need to check if the view_method is a generator or not
                data = yield data
            serialized = self.serialize(method, endpoint, data)
        except Exception as err:
            raise gen.Return(self.handle_error(err))

        status = self.status_map.get(self.http_methods[endpoint][method], OK)
        raise gen.Return(self.build_response(serialized, status=status))


