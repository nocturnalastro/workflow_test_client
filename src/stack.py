from copy import deepcopy
from collections import MutableMapping
from .exceptions import InvalidEmptyStackOperation
from .utils import deepmerge, deepdiff


class Stack:
    def __init__(self, head, tail=None, merge_strat=deepmerge):
        self.head = head
        self._tail = EmptyStack() if tail is None else tail
        self._merge_strat = merge_strat

    def push(self, item):
        return self.__class__(item, self)

    def update(self, update):
        self.head = self._merge_strat(self.head, update)
        return self

    def pop(self):
        return self._tail


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


class SparseStack:
    """The sparse stack is specific for the context use case where
    each layer is a variation on the optional than a completely
    new object. This allows the sparse stack only to store the changes between
    each layer.

    This requires one of two things either a flattening of the stack
    before returning the head or a facade which acts like the original data type
    to be which can do the flattening-like operations in real-time returned instead.
    This quickly becomes complex with nested data the flatten and return approach is
    used here

    Note: the assumed type with default merge_strat and diff_strat is dicts if you wish
    to use a different type you must pass your own merge and diff strats
    """

    def __init__(
        self,
        head,
        tail=None,
        merge_strat=deepmerge,
        diff_strat=deepdiff,
    ):
        self.merge_strat = merge_strat
        self.diff_strat = diff_strat
        self._head = diff_strat(head, tail)
        self._tail = EmptyStack() if tail is None else tail

    @property
    def head(self):
        res = self._head
        if not isinstance(self._tail, EmptyStack):
            res = self.merge_strat(self._tail.head, res)
        return deepcopy(res)

    def update(self, update):
        self._head = self.merge_strat(self._head, update)
        return self

    def push(self, item):
        return self.__class__(
            item,
            self,
            merge_strat=self.merge_strat,
            diff_strat=self.diff_strat,
        )

    def pop(self):
        return self._tail
