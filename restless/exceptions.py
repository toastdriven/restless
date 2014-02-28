from .constants import APPLICATION_ERROR, UNAUTHORIZED, NOT_FOUND, BAD_REQUEST
from .constants import METHOD_NOT_ALLOWED, METHOD_NOT_IMPLEMENTED


class RestlessError(Exception):
    """
    A common base exception from which all other exceptions in ``restless``
    inherit from.

    No special attributes or behaviors.
    """
    pass


class HttpError(RestlessError):
    """
    The foundational HTTP-related error.

    All other HTTP errors in ``restless`` inherit from this one.

    Has a ``status`` attribute. If present, ``restless`` will use this as the
    ``status_code`` in the response.

    Has a ``msg`` attribute. Has a reasonable default message (override-able
    from the constructor).
    """
    status = APPLICATION_ERROR
    msg = "Application Error"

    def __init__(self, msg=None):
        if not msg:
            msg = self.__class__.msg

        super(HttpError, self).__init__(msg)


class BadRequest(HttpError):
    status = BAD_REQUEST
    msg = "Bad request."


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
