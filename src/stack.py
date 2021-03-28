from .exceptions import InvalidEmptyStackOperation


class Stack:
    def __init__(self, head, tail=None):
        self.head = head
        self.tail = EmptyStack() if tail is None else tail

    def push(self, item):
        return self.__class__(item, self)

    def update(self, head):
        self.head = head
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

    def update(self, stack):
        self.stack = stack

    def push(self, value):
        self.update(self.stack.push(value))

    def pop(self):
        self.stack = self.stack.pop()
