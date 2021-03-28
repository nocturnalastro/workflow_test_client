from collections import namedtuple
import json
from typing import Any, ForwardRef, Optional, Type

from .validators import Validator
from .exceptions import CantClickDisabled
from .path import evaluator
from .stack import VirtualStack

__all__ = ("COMPONENTS", "Component")

Event = namedtuple("Event", ("action", "payload"))

jsonpath = evaluator()


class Component:
    def __init__(
        self,
        repos,
        name,
        type,
        preconditions=None,
        destination_path=None,
        add_event=lambda e: None,
    ):
        self.name: str = name
        self.task_type: str = type
        self.destination_path: str = destination_path
        self.preconditions: list[Validator] = (
            [self._process_validator(repos=repos, **p) for p in preconditions] if preconditions else []
        )
        self.add_event = add_event

    def _process_validator(self, repos, validator: str):
        return Validator(repos=repos, validator_name=validator)

    def _get_value(self, validator: Validator, context: dict):
        return validator.get_value(context=context, component=self)

    def _eval_validators(self, context, validators: list[Validator]):
        return all(validator.validate(component=self, context=context) for validator in validators)

    def validate(self, context: dict) -> None:
        pass

    def show(self, context):
        return self._eval_validators(context, self.preconditions)


class ComponentContextProxy:

    _component: Component
    _context_interface: VirtualStack

    def __init__(self, context_interface: VirtualStack, component: Component):
        self._component = component
        self._context_interface = context_interface

    @property
    def name(self) -> str:
        return self._component.name

    @property
    def is_value_component(self):
        return isinstance(self._component, ValueComponent)

    @property
    def is_button(self):
        return isinstance(self._component, Button)

    @property
    def destination_path(self):
        return self._component.destination_path

    @property
    def errors(self):
        return self._component.errors

    def validate(self) -> None:
        self._component.validate(context=self._context_interface.get_head())

    def get_value(self) -> Any:
        return self._component.get_value()

    def set_value(self, value: Any) -> None:
        self._component.set_value(value)

    def disabled(self) -> bool:
        return self._component.disabled(context=self._context_interface.get_head())

    def click(self) -> None:
        self._component.click(context=self._context_interface.get_head())

    def show(self) -> bool:
        return self._component.show(context=self._context_interface.get_head())

    def __repr__(self) -> str:
        return f"<Proxy for {repr(self._component).lstrip('<').rstrip('>')}>"


class ValueComponent(Component):
    _value: Any

    def __init__(self, repos, validator=None, **kwargs):
        super().__init__(repos=repos, **kwargs)
        if validator:
            self.validators = [self._process_validator(repos, v) for v in validator]
        else:
            self.validators = []
        self._value = None
        self._errors = []

    @property
    def errors(self):
        return self._errors.copy()

    def validate(self, context: dict) -> None:
        self._errors.clear()
        for validator in self.validators:
            if not validator.validate(component=self, context=context):
                msg = validator.get_message(component=self, context=context)
                self._errors.append(msg)

    def get_value(self) -> Any:
        return self._value

    def set_value(self, value: Any) -> None:
        self._value = value

    def disabled(self, context: dict) -> bool:
        raise NotImplementedError()

    def click(self, context: dict) -> None:
        raise NotImplementedError()


class Textbox(Component):
    pass


class Input(ValueComponent):
    def __init__(
        self,
        component_type=None,
        label=None,
        input_key=None,
        input_ref=None,
        output_ref=None,
        output=None,
        obscure=False,
        populate=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.component_type = component_type or self.__class__.__name__.lower()
        self.label = label or ""
        self.input_key = input_key
        self.input_ref = input_ref
        self.output_ref = output_ref
        self.output = output
        self.obscure = obscure
        self.populate = populate


class DateTime(Input):
    pass


class Clickable(ValueComponent):
    def set_value(self, value: Any):
        raise NotImplementedError()

    def disabled(self, context):
        return False

    def click(self, context):
        if not self.disabled(context):
            self._value = self.value
        else:
            raise CantClickDisabled()


class Button(Clickable):
    def __init__(
        self,
        action,
        style,
        text,
        value=True,
        load_values=None,
        show_confirmation=False,
        disabling_validators=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.action = action
        self.style = style
        self.text = text
        self.value = value
        self.show_confirmation = show_confirmation
        self.load_values = load_values
        if disabling_validators:
            self.disabling_validators = [self._process_validator(v) for v in disabling_validators]
        else:
            self.disabling_validators = []

    def disabled(self, context):
        return any(v.validate(context=context, component=self) for v in self.disabling_validators)

    def _get_payload(self) -> Optional[dict]:
        if self.destination_path and self._value:
            return jsonpath.set(context={}, path=self.destination_path, value=self._value)

    def click(self, context):
        super().click(context)
        if payload := self._get_payload():
            self.add_event(Event(action="update", payload=payload))
        self.add_event(Event(action=self.action, payload={}))


class DisplayData(Component):
    """
    Produces a display component which can list data in two different formats depending on the display_type,
    this can be "list" or "details" and requires the following formats provided as data:
        - "list": will list all the values provided, "data" should point to a list of strings
        - "details": requires a list of "{'label': '...', 'value': '...'}", "data" should
                 point to such an object in the context
    """

    __slots__ = [
        "data",
        "display_type",
        "title",
        "subtitle",
    ]

    def __init__(self, display_type, title, data, subtitle=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.data = data
        self.subtitle = subtitle
        self.display_type = display_type


# class OptionList(DisplayData):
#     """
#     This component is a selectable analogue to the DisplayData component.
#     Elements are displayed as in the "details" case of  DisplayData,
#     and upon selection a defined value is added to the context.
#     This requires data to be a list of
#         {
#             'details': [
#                     {'label': 'label1', 'value': 'value1'},
#                     {'label': 'label2', 'value': 'value2'}
#                 ],
#             'submitted_value': '...',
#             'submitted_key': '...',
#         }
#         where,
#         'details': a list whose elements are rendered as a label and
#             value,
#         'submitted_value': the value submitted upon selection of
#         the option,
#         'submitted_key': a value to submit is taken from the context
#         attribute corresponding to this key.
#         Note, 'submitted_value' and 'submitted_key' are mutually exclusive.
#     """

#     def __init__(self, display_type, title, data, subtitle, **kwargs):
#         super().__init__(display_type, title, data, subtitle=subtitle, **kwargs)
#         self._values = self._process_values()

#     def _process_values(self):
#         return {
#             d["label"]: d["value"]
#             for d in self._task["details"]
#         }

#     def set_value(self, value: Any):
#         self._value = self._values[value]

# class Modal(Component):
#     """
#     A data structure to render a modal popup on the frontend, which itself
#     can contain components.
#     """

#     __slots__ = [
#         "components",
#         "trigger_conditions",
#         "title"
#     ]

#     def __init__(self, title, components, trigger_conditions=None, **kwargs):
#         super().__init__(**kwargs)
#         self.title = title
#         self.components = components
#         self.trigger_conditions = trigger_conditions or []

# class Checkbox(ValueComponent):
#     """
#     - "data": requires a list of "{'id': 1, 'label': '...', 'value': '...'}"
#     """

#     __slots__ = [
#         "data",
#         "target",
#         "title"
#     ]

#     def __init__(self, title, data, target, **kwargs):
#         super().__init__(**kwargs)
#         self.title = title
#         self.data = data
#         self.target = target


class MessageBox(Component):
    def __init__(self, message, size=None, **kwargs):
        super().__init__(**kwargs)
        self.template = message["template"]
        self.type = message["type"]
        self.size = size


class Toggle(Clickable):
    __slots__ = [
        "style",
        "preconditions",
        "value",
        "label",
    ]

    def __init__(self, style, label, value=None, **kwargs):
        super().__init__(**kwargs)
        self.style = style
        self.label = label
        self.value = value


class Selection(ValueComponent):
    __slots__ = ["style", "is_required", "options_key", "options_values", "label"]

    def __init__(
        self,
        label,
        style="default",
        is_required=False,
        options_key=None,
        options_values=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.style = style
        self.label = label
        self.is_required = is_required
        self.options_key, self.options_values = self.get_options(options_key, options_values)


class Image(Component):
    __slots__ = [
        "url",
    ]

    def __init__(self, url, **kwargs):
        super().__init__(**kwargs)
        self.url = url


# class Repeat(Component):
#     """
#     A meta component which can be used to repeat the same field.

#     Args:
#         times_to_repeat: Int
#             number of times the field should be repeated
#         times_to_repeat_path: Str:
#             a jsonpath to look up how many times the field should be repeated
#         components: List[List[Component]]
#             a list of rows of components in the group
#     """

#     __slots__ = [
#         "times_to_repeat",
#         "times_to_repeat_path",
#         "components",
#     ]

#     def __init__(self, components, times_to_repeat=None, times_to_repeat_path=None, **kwargs):
#         self._validate_args(times_to_repeat, times_to_repeat_path)
#         super().__init__(**kwargs)
#         self.components = components
#         self.times_to_repeat = times_to_repeat
#         self.times_to_repeat_path = times_to_repeat_path


def not_implemented(*args, **kwargs):
    raise NotImplementedError()


COMPONENTS = {
    "textbox": Textbox,
    "input": Input,
    "datetime": DateTime,
    "button": Button,
    "displaydata": DisplayData,
    "optionlist": not_implemented,
    "modal": not_implemented,
    "checkbox": not_implemented,
    "message_box": MessageBox,
    "toggle": Toggle,
    "selection": Selection,
    "image": Image,
    "repeat": not_implemented,
}
