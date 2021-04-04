from collections import defaultdict
import enum


class UrlMethod(enum.Enum):
    GET = "get"
    POST = "post"


class MockServerErrorResponce:
    def __init__(self, msg) -> None:
        self.msg = msg


class MockServer:
    def __init__(self) -> None:
        self._endpoints = {}

    def register_handler(self, url, method, handler):
        self._endpoints[(url, method)] = handler

    def add_workflow(self, url, workflow):
        self._endpoints[(url, UrlMethod.GET)] = lambda _a: workflow

    def _lookup(self, url, method, args):
        key = (url, method)
        if key in self._endpoints:
            return self._endpoints[key](args)
        return MockServerErrorResponce("not found")

    def get(self, url):
        return self._lookup(url, UrlMethod.GET, None)

    def post(self, url, args):
        return self._lookup(url, UrlMethod.GET, args)