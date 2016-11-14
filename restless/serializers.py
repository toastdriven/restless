from .exceptions import BadRequest
from .utils import json, MoreTypesJSONEncoder


class Serializer(object):
    """
    A base serialization class.

    Defines the protocol expected of a serializer, but only raises
    ``NotImplementedError``.

    Either subclass this or provide an object with the same
    ``deserialize/serialize`` methods on it.
    """
    def deserialize(self, body):
        """
        Handles deserializing data coming from the user.

        Should return a plain Python data type (such as a dict or list)
        containing the data.

        :param body: The body of the current request
        :type body: string

        :returns: The deserialized data
        :rtype: ``list`` or ``dict``
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def serialize(self, data):
        """
        Handles serializing data being sent to the user.

        Should return a plain Python string containing the serialized data
        in the appropriate format.

        :param data: The body for the response
        :type data: string

        :returns: A serialized version of the data
        :rtype: string
        """
        raise NotImplementedError("Subclasses must implement this method.")


class JSONSerializer(Serializer):
    def deserialize(self, body):
        """
        The low-level deserialization.

        Underpins ``deserialize``, ``deserialize_list`` &
        ``deserialize_detail``.

        Has no built-in smarts, simply loads the JSON.

        :param body: The body of the current request
        :type body: string

        :returns: The deserialized data
        :rtype: ``list`` or ``dict``
        """
        try:
            if isinstance(body, bytes):
                return json.loads(body.decode('utf-8'))
            return json.loads(body)
        except ValueError:
            raise BadRequest('Request body is not valid JSON')

    def serialize(self, data):
        """
        The low-level serialization.

        Underpins ``serialize``, ``serialize_list`` &
        ``serialize_detail``.

        Has no built-in smarts, simply dumps the JSON.

        :param data: The body for the response
        :type data: string

        :returns: A serialized version of the data
        :rtype: string
        """
        return json.dumps(data, cls=MoreTypesJSONEncoder)
