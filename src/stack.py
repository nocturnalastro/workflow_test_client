from copy import deepcopy
from .exceptions import InvalidEmptyStackOperation
from .utils import deepmerge


class Stack:
    def __init__(self, head, tail=None, merge_strat=deepmerge):
        self.head = head
        self.tail = EmptyStack() if tail is None else tail
        self._merge_strat = merge_strat

    def push(self, item):
        return self.__class__(item, self)

    def update(self, update):
        self.head = self._merge_strat(self.head, update)
        return self

    def pop(self):
        return self.tail


class EmptyStack:
    @property
    def head(self):
        raise InvalidEmptyStackOperation()

    @property
    def tail(self):
        raise InvalidEmptyStackOperation()

    def pop(self):
        raise InvalidEmptyStackOperation()

    def update(self, head):
        return Stack(head)

    def push(self, item):
        return Stack(item)


class VirtualStack:
    def __init__(self, initial):
        self.stack = initial

    def get_head(self):
        return self.get().head

    def get(self):
        return self.stack

    def update(self, value):
        self.stack = self.stack.update(value)

    def push(self, value):
        self.stack = self.stack.push(value)

    def pop(self):
        self.stack = self.stack.pop()

    def push_head_copy(self):
        self.push(self.get_head())
