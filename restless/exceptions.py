class RestlessError(Exception):
    pass


class HttpError(RestlessError):
    status = 500
    msg = "Application Error"

    def __init__(self, msg=None):
        if not msg:
            msg = self.__class__.msg

        super(HttpError, self).__init__(msg)


class NotFound(HttpError):
    status = 404
    msg = "Resource not found."


class MethodNotAllowed(HttpError):
    status = 405
    msg = "The specified HTTP method is not allowed."


class MethodNotImplemented(HttpError):
    status = 501
    msg = "The specified HTTP method is not implemented."
