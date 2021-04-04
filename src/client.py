from collections import namedtuple

from .exceptions import InvalidEmptyStackOperation
from .parser import json_parser
from .stack import Stack, VirtualStack
from .tasks import TASK_TYPES, Flow
from .context import ExecutionContext

Repos = namedtuple("Repos", ("components", "validators", "flows"))


class TestClient:
    def __init__(self, workflow, workflow_parser=json_parser):
        self.raw_workflow = workflow
        parts = workflow_parser(workflow)
        self._interupt_tasks = set()
        self._starting_flow = parts.starting_flow

        self._initial_context = ExecutionContext(
            initial_state=parts.context,
            repos=Repos(
                components=parts.components,
                validators=parts.validators,
                flows=parts.flows,
            ),
        )

        TASK_TYPES["flow"](
            execution_context=self._initial_context,
            task={"name": parts.starting_flow, "type": "flow"},
        )

        self.context_stack = VirtualStack(Stack(self._initial_context))
        self._initial_context.register_stack_handle(self.context_stack)

    def get_task(self):
        while True:  # Keep doing up the call stack until we reach the end
            try:
                context = self.context_stack.get_head()
                return context.flow.get_task(self._interupt_tasks)
            except StopIteration as s:
                if context == self._initial_context:
                    self.context_stack.pop()
                continue
            except InvalidEmptyStackOperation:
                return None
