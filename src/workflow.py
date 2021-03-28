from .stack import VirtualStack, Stack
from .tasks import TASK_TYPES
from .exceptions import InvalidEmptyStackOperation


class Repos:
    def __init__(self, components, validators, flows):
        self.components = components
        self.validators = validators
        self.flows = flows
        self.interactors = {}

    def set_interactors(self, interactors):
        self.interactors = interactors


class Workflow:
    _task_types = TASK_TYPES

    def __init__(self, entry_point, repos, initial_context):
        self.context_interface = VirtualStack(Stack(initial_context))
        initial_flow = self._task_types["flow"](
            context_interface=self.context_interface,
            task=repos.flows[entry_point],
            repos=repos,
        )
        self._interupt_tasks = []
        self.call_stack_interface = VirtualStack(Stack(initial_flow))
        initial_flow.set_call_stack_interface(self.call_stack_interface)

    def set_task_breakpoint(self, task_name):
        """Set a task to return in get task which doesn't require input"""
        self._interupt_tasks.append(task_name)

    def get_task(self):
        while True:  # Keep doing up the call stack until we reach the end
            try:
                return self.call_stack_interface.get_head().get_task(self._interupt_tasks)
            except StopIteration as s:
                pass  # Allow stack pop to complete
            except InvalidEmptyStackOperation:
                return None
