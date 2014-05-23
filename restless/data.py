class Data(object):
    def __init__(self, value, should_prepare=True, prepare_with=None):
        """
        A container object that carries meta information about the data.

        ``value`` should be the data to be returned to the client. This may
        be post-processed.

        ``should_prepare`` determines whether additional post-processing
        should occur & should be boolean. This is useful when returning objects
        or with complex requirements. Default is ``True``.

        ``prepare_with`` is reserved for future use in specifying a custom
        callable. Default is ``None`` (no custom callable).
        """
        self.value = value
        self.should_prepare = should_prepare
        self.prepare_with = prepare_with
