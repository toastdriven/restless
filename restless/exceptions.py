from .constants import (APPLICATION_ERROR, UNAUTHORIZED, NOT_FOUND, BAD_REQUEST,
                        FORBIDDEN, NOT_ACCEPTABLE, GONE, PRECONDITION_FAILED,
                        CONFLICT, UNSUPPORTED_MEDIA_TYPE, EXPECTATION_FAILED,
                        I_AM_A_TEAPOT, TOO_MANY_REQUESTS, UNPROCESSABLE_ENTITY,
                        UNAVAILABLE_FOR_LEGAL_REASONS, FAILED_DEPENDENCY,
                        LOCKED)
from .constants import METHOD_NOT_ALLOWED, METHOD_NOT_IMPLEMENTED, UNAVAILABLE


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


class Forbidden(HttpError):
    status = FORBIDDEN
    msg = "Permission denied."


class NotFound(HttpError):
    status = NOT_FOUND
    msg = "Resource not found."


class MethodNotAllowed(HttpError):
    status = METHOD_NOT_ALLOWED
    msg = "The specified HTTP method is not allowed."


class NotAcceptable(HttpError):
    # TODO: make serializers handle it?
    status = NOT_ACCEPTABLE
    msg = "Unable to send content specified on the request's Accept header(s)."


class Conflict(HttpError):
    status = CONFLICT
    msg = "There was a conflict when processing the request."


class Gone(HttpError):
    status = GONE
    msg = "Resource removed permanently."


class PreconditionFailed(HttpError):
    status = PRECONDITION_FAILED
    msg = "Unable to satisfy one or more request preconditions."


class UnsupportedMediaType(HttpError):
    status = UNSUPPORTED_MEDIA_TYPE
    msg = "Type of media provided on request is not supported."


class ExpectationFailed(HttpError):
    status = EXPECTATION_FAILED
    msg = "Unable to satisfy requirements of Expect header."


class IAmATeapot(HttpError):
    status = I_AM_A_TEAPOT
    msg = "This is a teapot; do not attempt to brew coffee with it."


class UnprocessableEntity(HttpError):
    status = UNPROCESSABLE_ENTITY
    msg = "Request cannot be followed due to a semantic error."


class Locked(HttpError):
    status = LOCKED
    msg = "Resource is locked."


class FailedDependency(HttpError):
    status = FAILED_DEPENDENCY
    msg = "Request failed due to a previous failed request."


class TooManyRequests(HttpError):
    status = TOO_MANY_REQUESTS
    msg = "There was a conflict when processing the request."


class UnavailableForLegalReasons(HttpError):
    status = UNAVAILABLE_FOR_LEGAL_REASONS
    msg = "Resource made unavailable by a legal decision."


class MethodNotImplemented(HttpError):
    status = METHOD_NOT_IMPLEMENTED
    msg = "The specified HTTP method is not implemented."


class Unavailable(HttpError):
    status = UNAVAILABLE
    msg = "There was a conflict when processing the request."
