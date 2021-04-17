from collections import namedtuple

from .exceptions import InvalidEmptyStackOperation
from .parser import json_parser
from .stack import EmptyStack, Stack, VirtualStack
from .tasks import TASK_TYPES
from .context import ExecutionContext
from . import history

Repos = namedtuple("Repos", ("components", "validators", "flows"))


class TestClient:
    def __init__(self, mock_server, workflow_url, workflow_parser=json_parser):
        self._server = mock_server
        self._parser = workflow_parser
        self._interupt_tasks = set()
        self._load_workflow(workflow_url)

    def _load_workflow(self, url):
        self.raw_workflow = self._server.get(url)
        self._initialise_flow(self._parser(self.raw_workflow))

    def _initialise_flow(self, parts):
        self._starting_flow = parts.starting_flow
        self._history_stack = VirtualStack(EmptyStack())
        self._initial_context = ExecutionContext(
            initial_state=parts.context,
            repos=Repos(
                components=parts.components,
                validators=parts.validators,
                flows=parts.flows,
            ),
            event_handler=self._handle_event,
            history_handle=self._history_stack,
        )

        TASK_TYPES["flow"](
            execution_context=self._initial_context,
            task={"name": parts.starting_flow, "type": "flow"},
        )

        self.context_stack = VirtualStack(Stack(self._initial_context))
        self._initial_context.register_stack_handle(self.context_stack)
        self._initial_context.start()

    def _handle_event(self, type, data):
        if type == "redirect":
            self._load_workflow(data["url"])
        if type == "save_history":
            self._history_stack.push(
                history.Entry(execution_context=data["execution_context"])
            )

    def set_task_breakpoint(self, task_name):
        self._interupt_tasks.add(task_name)

    def get_task(self):
        while True:  # Keep doing up the call stack until we reach the end
            try:
                context = self.context_stack.get_head()
                return context.flow.get_task(self._interupt_tasks)
            except StopIteration as s:
                if context == self._initial_context:
                    self._initial_context.stop()
                continue
            except InvalidEmptyStackOperation:
                return None
