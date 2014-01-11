class RestlessError(Exception):
    pass


class NotFound(RestlessError):
    status = 404


class MethodNotAllowed(RestlessError):
    status = 405


class MethodNotImplemented(RestlessError):
    status = 501
