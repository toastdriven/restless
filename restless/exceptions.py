from .constants import APPLICATION_ERROR, UNAUTHORIZED, NOT_FOUND
from .constants import METHOD_NOT_ALLOWED, METHOD_NOT_IMPLEMENTED


class RestlessError(Exception):
    pass


class HttpError(RestlessError):
    status = APPLICATION_ERROR
    msg = "Application Error"

    def __init__(self, msg=None):
        if not msg:
            msg = self.__class__.msg

        super(HttpError, self).__init__(msg)


class Unauthorized(HttpError):
    status = UNAUTHORIZED
    msg = "Unauthorized."


class NotFound(HttpError):
    status = NOT_FOUND
    msg = "Resource not found."


class MethodNotAllowed(HttpError):
    status = METHOD_NOT_ALLOWED
    msg = "The specified HTTP method is not allowed."


class MethodNotImplemented(HttpError):
    status = METHOD_NOT_IMPLEMENTED
    msg = "The specified HTTP method is not implemented."
