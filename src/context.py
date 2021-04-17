from copy import deepcopy
from .registry import TASK_TYPES
from .utils import deepmerge


class ExecutionContext:
    def __init__(
        self,
        initial_state,
        repos,
        event_handler,
        history_handle,
        flow=None,
        stack_handle=None,
        task=None,
        position=0,
    ):
        self._state = initial_state
        self.repos = repos
        self._result = {}
        self.flow = flow
        self.task = task
        self._stack_handle = stack_handle
        self._event_handler = event_handler
        self._history_handle = history_handle
        self.position = position

    def __enter__(self):
        self._stack_handle.push(self)
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

    def merge_result_into_state(self):
        self._state = deepmerge(self._state, self._result)

    @property
    def result(self):
        return deepcopy(self._result)

    def new_context(self, position=0):
        context = ExecutionContext(
            initial_state=self.state,
            repos=self.repos,
            flow=self.flow,
            stack_handle=self._stack_handle,
            event_handler=self.register_event,  # To allow for even interception
            history_handle=self._history_handle,
            position=position,
        )
        return context

    def register_task(self, task):
        self.task = task
        if isinstance(task, TASK_TYPES["flow"]):
            self.flow = task

    def _get_history_head(self):
        return self._history_handle.get_head()

    def register_event(self, type, data):
        if type == "back":
            history_entry = self._get_history_head()
            if self.task == self.flow == history_entry.execution_context.flow:
                self.flow.re_init_iter(
                    execution_context=history_entry.execution_context
                )
                return True
            else:
                # Target of back is not in this flow so
                # exit this execution conext
                self.stop()
        return self._event_handler(type, data)

    def start(self):
        return self.__enter__()

    def stop(self):
        return self.__exit__()