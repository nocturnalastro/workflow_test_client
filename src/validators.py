from typing import Any
from .path import evaluator
from .templating import process_template

jsonpath = evaluator()


class Validator:
    def __init__(self, validator_name, execution_context, component):
        self._execution_context = execution_context
        self._component = component
        self._config = self._execution_context.repos.validators[validator_name]
        self._config["name"] = validator_name

    def _get_value(self, context: dict, component):
        if self._config.get("value_path"):
            return jsonpath.get(context=context, path=self._config["value_path"])
        return component.get_value()

    def _get_validator_value(self, context):
        if self._config.get("validator_key"):
            return jsonpath.get(context=context, path=self._config["validator_key"])
        return self._config.get("validator_value")

    def _validate(self, value: Any, validator_value: Any):
        func = VALIDATORS[self._config["type"]]
        return func(value, validator_value)

    def validate(self):
        context = self._execution_context.state
        component = self._component
        return self._validate(
            value=self._get_value(context=context, component=component),
            validator_value=self._get_validator_value(context=context),
        )

    def get_message(self):
        return process_template(
            template=self._config["message"]["template"],
            context=self._execution_context.state,
        )


def is_str_length(value, min=0, max=None):
    value = str(value or "")
    length = len(value)
    res = length >= (min or 0)
    if max is not None:
        res = res and length <= max
    return res


VALIDATORS = {
    "isLength": is_str_length,
}
