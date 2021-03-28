from copy import deepcopy
from typing import List
from .components import COMPONENTS, Component, ComponentContextProxy
from .path import evaluator
from . import utils


jsonpath = evaluator()

__all__ = (
    "Task",
    "TASK_TYPES",
)


class Task:
    _requires_input = False

    def __init__(self, context_interface, task, repos, call_stack_interface=None):
        self._task = task
        self._context_interface = context_interface
        self._repos = repos
        self._local_context = deepcopy(self._context_interface.get_head())
        self._call_stack_interface = call_stack_interface
        self._complete = False
        self._exit_reason = "success"

    @property
    def name(self):
        return self._task["name"]

    @property
    def requires_input(self):
        return self._requires_input and not self._complete

    def get_new_context(self):
        return self._local_context

    def process(self):
        stack = self._context_interface.get()
        self._context_interface.update(stack.update(self.get_new_context()))


class Screen(Task):
    _requires_input = True

    def __init__(self, context_interface, task, repos, call_stack_interface):
        super().__init__(context_interface, task, repos, call_stack_interface=call_stack_interface)
        self._components = self._process_component_lookups()
        self._events = []

    def _init_component(self, component_config: dict):
        component_config["add_event"] = lambda e: self._events.append(e)
        return ComponentContextProxy(
            context_interface=self._context_interface,
            component=COMPONENTS[component_config["type"]](repos=self._repos, **component_config),
        )

    def _process_component_lookups(self) -> list[Component]:
        components = {}
        for row in self._task["components"]:
            for lookup in row:
                name = lookup["name"]
                components[name] = self._init_component(
                    component_config=self._repos.components[name] | lookup
                )
        return components

    def get_components(self) -> dict[str, Component]:
        return dict(filter(lambda c: c[1].show(), self._components.items()))

    def set(self, field, value):
        components = self.get_components()
        components[field].set_value(value)

    def click(self, button_name):
        components = self.get_components()
        components[button_name].click()
        self._process_events()

    @property
    def errors(self):
        return {
            name: component.errors for name, component in self.get_components().items() if component.errors
        }

    @property
    def result(self):
        res = {}
        for component in self.get_components().values():
            if component.is_value_component and not component.is_button:
                res = jsonpath.set(
                    context=res,
                    path=component.destination_path,
                    value=component.get_value(),
                )
        return res

    def _process_field_validators(self):
        for component in self.get_components().values():
            component.validate()

    def _process_events(self):
        for n, event in enumerate(self._events):
            if event.action == "submit":
                self._process_field_validators()
                if not self.errors:
                    self._complete = True
            elif event.action == "next":
                self._complete = True
            elif event.action == "update":
                self._local_context = utils.deepmerge(self._local_context, event.payload)

    def get_new_context(self):
        return utils.deepmerge(
            super().get_new_context(),
            self.result,
        )


class JsonRpc(Task):
    _requires_input = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._payload = self._get_playload()

    def get_endpoint(self):
        return self._task["url"]

    def _process_instruction(self, instruction):
        if "value" in instruction:
            value = instruction["value"]
        elif "key" in instruction:
            value = jsonpath.get_one(
                context=self._context_interface.get_head(),
                path=instruction["key"],
            )
        else:
            raise KeyError("Value or key not in instruction")

        return jsonpath.set(context={}, path=instruction["result_key"], value=value)

    def _get_playload(self):
        payload = deepcopy(self._task["payload"])
        for instruction in self._task["payload_paths"]:
            payload = utils.deepmerge(payload, self._process_instruction(instruction))
        return payload

    def get_payload(self):
        return self._payload

    @property
    def requires_input(self):
        # If theres not destination_path then we don't need input
        if not self._task.get("destination_path", False):
            return False
        return super().requires_input

    def set_result(self, result):
        self._local_context = jsonpath.set(
            context=self._local_context,
            path=self._task["destination_path"],
            value=result,
        )

    # def get_new_context(self):
    #     context = super().get_new_context()
    #     for


class Update(Task):
    task_type = "update"


class Redirect(Task):
    task_type = "redirect"


class Condition:
    task_type = "condition"


class DomainParam:
    task_type = "domain_param"


class Flow(Task):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._task_iter = None
        if self._call_stack_interface is not None:
            self._push_call_stack()

    def _create_context(self):
        self._context_interface.push(self._local_context)

    def _destroy_context(self):
        self._context_interface.pop()

    def _push_call_stack(self):
        if self._call_stack_interface.get_head() != self:
            self._call_stack_interface.push(self)

    def _pop_call_stack(self):
        if self._call_stack_interface.get_head() == self:
            self._call_stack_interface.pop()

    def set_call_stack_interface(self, call_stack_interface):
        self._call_stack_interface = call_stack_interface
        self._push_call_stack()

    def _get_task_instance(self, task):
        return TASK_TYPES[task["type"]](
            task=task,
            repos=self._repos,
            context_interface=self._context_interface,
            call_stack_interface=self._call_stack_interface,
        )

    def _process_instruction(self, instruction, context):
        if "value" in instruction:
            value = instruction["value"]
        elif "key" in instruction:
            value = jsonpath.get_one(
                context=self._local_context,
                path=instruction["key"],
            )
        else:
            raise KeyError("Value or key not in instruction")

        return jsonpath.set(context={}, path=instruction["result_key"], value=value)

    def get_new_context(self):
        result = {}
        for path in self._task["result_paths"]:
            # Note _process_instruction uses local_context which is the
            # the context stack within the task
            result = utils.deepmerge(result, self._process_instruction(path))

        return jsonpath.set(
            # this will likely be the parent stack at this point
            context=self._context_interface.get_head(),
            path=self._task["destination_path"],
            value=result,
        )

    def _input_task_iter(self, interupt_tasks=None):
        if interupt_tasks is None:
            interupt_tasks = set()

        self._create_context()
        for task in self._task["tasks"]:
            inst = self._get_task_instance(task)
            if inst.name in interupt_tasks:
                yield inst
            while inst.requires_input:
                yield inst
            inst.process()
            if isinstance(inst, Event) and inst._task["action"] == "break":
                break

        self._destroy_context()
        self._complete = True
        self._pop_call_stack()

    def get_task(self, interupt_tasks=None):
        if self._task_iter is None:
            self._task_iter = self._input_task_iter(interupt_tasks)
        return next(self._task_iter)


class WhileLoop(Flow):
    pass


class ForLoop(Flow):
    pass


class ClearDomainParams(Task):
    pass


class Event(Task):
    pass


TASK_TYPES = {
    "screen": Screen,
    "jsonrpc": JsonRpc,
    "flow": Flow,
    "while_loop": WhileLoop,
    "for_loop": ForLoop,
    "update": Update,
    "redirect": Redirect,
    "condition": Condition,
    "domain_params": DomainParam,
    "clear_domain_params": ClearDomainParams,
    "event": Event,
}