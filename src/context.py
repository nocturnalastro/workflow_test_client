from copy import deepcopy
from .registry import TASK_TYPES
from .utils import deepmerge


class ExecutionContext:
    def __init__(
        self,
        initial_state,
        repos,
        event_handler,
        flow=None,
        stack_handle=None,
    ):
        self._state = initial_state
        self.repos = repos
        self._result = {}
        self.flow = flow
        self._stack_handle = stack_handle
        self._event_handler = event_handler

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self._stack_handle.pop()

    def register_stack_handle(self, handle):
        self._stack_handle = handle

    @property
    def state(self):
        return deepcopy(self._state)

    def update_state(self, update: dict):
        self._state = deepmerge(self._state, update)

    def update_result(self, update: dict):
        self._result = deepmerge(self._result, update)

    @property
    def result(self):
        return deepcopy(self._result)

    def new_context(self):
        context = ExecutionContext(
            initial_state=self.state,
            repos=self.repos,
            flow=self.flow,
            stack_handle=self._stack_handle,
            event_handler=self._event_handler,
        )
        self._stack_handle.push(context)
        return context

    def register_task(self, task):
        if isinstance(task, TASK_TYPES["flow"]):
            self.flow = task

    def register_event(self, type, data):
        self._event_handler(type, data)