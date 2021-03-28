from typing import Any
from .path import evaluator

jsonpath = evaluator()


class Validator:
    def __init__(self, repos, validator_name):
        self._config = repos.validators[validator_name]
        self._config["name"] = validator_name

    def get_value(self, context: dict, component):
        if self._config.get("value_path"):
            return jsonpath.get(context=context, path=self._config["value_path"])
        return component.get_value()

    def get_validator_value(self, context):
        if self._config.get("validator_key"):
            return jsonpath.get(context=context, path=self._config["validator_key"])
        return self._config.get("validator_value")

    def _validate(self, value: Any, validator_value: Any):
        func = VALIDATORS[self._config["type"]]
        return func(value, validator_value)

    def validate(self, context, component):
        return self._validate(
            value=self.get_value(context=context, component=component),
            validator_value=self.get_validator_value(context=context),
        )

    def get_message(self, context, component):
        return self._config["message"]["template"]


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
