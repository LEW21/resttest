import json
from datetime import datetime

import requests

from resttest.schema import make_schemaless_object, serialize, unserialize


class HTTPResponse(Exception):
    """HTTP response"""

    def __init__(self, data):
        self.data = data


class HTTP200_OK(HTTPResponse):
    code = 200
    reason = 'OK'

    def __init__(self, data):
        if data is None:
            raise ValueError('Use HTTP204_NoContent for responses with no content')
        super().__init__(data)


OK = HTTP200_OK


class HTTP201_Created(HTTPResponse):
    code = 201
    reason = 'Created'


Created = HTTP201_Created


class HTTP204_NoContent(HTTPResponse):
    code = 204
    reason = 'No Content'

    def __init__(self, data):
        if data is not None:
            raise ValueError('Use HTTP200_OK for responses with content')
        super().__init__(data)


NoContent = HTTP204_NoContent


class HTTP303_SeeOther(HTTPResponse):
    code = 303
    reason = 'See Other'


SeeOther = HTTP303_SeeOther


class HTTP400_BadRequest(HTTPResponse):
    code = 400
    reason = 'Bad Request'


BadRequest = HTTP400_BadRequest


class HTTP401_NotAuthenticated(HTTPResponse):
    code = 401
    reason = 'Not Authenticated'


NotAuthenticated = HTTP401_NotAuthenticated


class HTTP403_Forbidden(HTTPResponse):
    code = 403
    reason = 'Forbidden'


Forbidden = HTTP403_Forbidden


class HTTP404_NotFound(HTTPResponse):
    code = 404
    reason = 'Not Found'


NotFound = HTTP404_NotFound


class HTTP405_MethodNotAllowed(HTTPResponse):
    code = 405
    reason = 'Method Not Allowed'


MethodNotAllowed = HTTP405_MethodNotAllowed


class HTTP409_Conflict(HTTPResponse):
    code = 409
    reason = 'Conflict'


Conflict = HTTP405_MethodNotAllowed


class HTTP500_InternalServerError(HTTPResponse):
    code = 500
    reason = 'Internal Server Error'


InternalServerError = HTTP500_InternalServerError


class HTTP501_NotImplemented(HTTPResponse):
    code = 501
    reason = 'Not Implemented'


NotImplemented = HTTP501_NotImplemented

responses = {
    200: HTTP200_OK,
    201: HTTP201_Created,
    204: HTTP204_NoContent,
    303: HTTP303_SeeOther,
    400: HTTP400_BadRequest,
    401: HTTP401_NotAuthenticated,
    403: HTTP403_Forbidden,
    404: HTTP404_NotFound,
    405: HTTP405_MethodNotAllowed,
    409: HTTP409_Conflict,
    500: HTTP500_InternalServerError,
    501: HTTP501_NotImplemented,
}


class HTTPSession:
    def __init__(self):
        self._requests_session = requests.Session()

    @property
    def headers(self):
        return self._requests_session.headers

    @property
    def cookies(self):
        return self._requests_session.cookies

    def request(self, method, url, data = None, return_type = None, ignore_response_data = False, ignore_error_data = False) -> HTTPResponse:
        resp = self._requests_session.request(
            method,
            url,
            headers = {'Content-Type': 'application/json'} if data is not None else {},
            data = json.dumps(serialize(data)) if data is not None else None,
            allow_redirects = True,
        )

        if return_type and resp.status_code < 400:
            resp_content = unserialize(return_type, resp.json()) if not ignore_response_data else ...
        else:
            if ignore_error_data:
                resp_content = ...
            elif not resp.content:
                resp_content = None
            else:
                resp_content = make_schemaless_object(resp.json())

        response = responses[resp.status_code](resp_content)

        if response.code >= 400:
            raise response

        return response

    def get(self, url, return_type = None, ignore_response_data = False, ignore_error_data = False) -> HTTPResponse:
        return self.request('GET', url, return_type = return_type, ignore_response_data = ignore_response_data, ignore_error_data = ignore_error_data)

    def post(self, url, data, return_type = None, ignore_response_data = False, ignore_error_data = False) -> HTTPResponse:
        return self.request('POST', url, data, return_type = return_type, ignore_response_data = ignore_response_data, ignore_error_data = ignore_error_data)

    def patch(self, url, data, return_type = None, ignore_response_data = False, ignore_error_data = False) -> HTTPResponse:
        return self.request('PATCH', url, data, return_type = return_type, ignore_response_data = ignore_response_data, ignore_error_data = ignore_error_data)

    def put(self, url, data, return_type = None, ignore_response_data = False, ignore_error_data = False) -> HTTPResponse:
        return self.request('PUT', url, data, return_type = return_type, ignore_response_data = ignore_response_data, ignore_error_data = ignore_error_data)

    def delete(self, url, return_type = None, ignore_response_data = False, ignore_error_data = False) -> HTTPResponse:
        return self.request('DELETE', url, return_type = return_type, ignore_response_data = ignore_response_data, ignore_error_data = ignore_error_data)
