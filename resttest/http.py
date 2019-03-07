import requests


class NiceDict(dict):
    def __init__(self, normal_dict):
        super().__init__([(k, (NiceDict(v) if isinstance(v, dict) else v)) for k, v in normal_dict.items()])

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(attr)


class HTTPResponse(Exception):
    """HTTP response"""

    def __init__(self, data):
        self.data = NiceDict(data) if isinstance(data, dict) else data
        #self.data = data


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


class HTTP400_BadRequest(HTTPResponse):
    code = 400
    reason = 'Bad Request'


BadRequest = HTTP400_BadRequest


class HTTP404_NotFound(HTTPResponse):
    code = 404
    reason = 'Not Found'


NotFound = HTTP404_NotFound


class HTTP405_MethodNotAllowed(HTTPResponse):
    code = 405
    reason = 'Method Not Allowed'


MethodNotAllowed = HTTP405_MethodNotAllowed


class HTTP500_InternalServerError(HTTPResponse):
    code = 500
    reason = 'Internal Server Error'


responses = {
    200: HTTP200_OK,
    201: HTTP201_Created,
    204: HTTP204_NoContent,
    400: HTTP400_BadRequest,
    404: HTTP404_NotFound,
    405: HTTP405_MethodNotAllowed,
    500: HTTP500_InternalServerError,
}


class HTTPSession:
    def __init__(self):
        self._requests_session = requests.Session()

    def request(self, method, url, data = None) -> HTTPResponse:
        resp = self._requests_session.request(method, url, json = data)
        response = responses[resp.status_code](resp.json() if resp.status_code not in [204, 500] else None)

        if response.code >= 400:
            raise response

        return response

    def get(self, url) -> HTTPResponse:
        return self.request('GET', url)

    def post(self, url, data) -> HTTPResponse:
        return self.request('POST', url, data)

    def patch(self, url, data) -> HTTPResponse:
        return self.request('PATCH', url, data)

    def put(self, url, data) -> HTTPResponse:
        return self.request('PUT', url, data)

    def delete(self, url) -> HTTPResponse:
        return self.request('DELETE', url)
