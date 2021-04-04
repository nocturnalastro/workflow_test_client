from collections import defaultdict
import enum


class Methods(enum.Enum):
    GET = "get"
    POST = "post"


class MockServerErrorResponce(Exception):
    pass


class MockServer:
    def __init__(self) -> None:
        self._endpoints = {}

    def register_handler(self, url, method, handler):
        self._endpoints[(url, method)] = handler

    def _lookup(self, url, method, args):
        key = (url, method)
        if key in self._endpoints:
            return self._endpoints[key](args)
        raise MockServerErrorResponce(
            f"Handler for {url} not found for method {method}"
        )

    def get(self, url):
        return self._lookup(url, Methods.GET, None)

    def post(self, url, args):
        return self._lookup(url, Methods.POST, args)