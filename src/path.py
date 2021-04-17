from jsonpath_ng import parse, jsonpath
from copy import deepcopy


class UnhandledSetter(ValueError):
    pass


class NotFoundInContext(KeyError):
    pass


class JSONPath:
    def _get_expr(self, path):
        if isinstance(path, jsonpath.Child):
            return path
        return parse(path)

    def get(self, context, path):
        return [d.value for d in self._get_expr(path).find(context)]

    def get_one(self, context, path):
        values = self.get(context, path)
        if not values:
            raise NotFoundInContext()
        else:
            return values[0]

    @staticmethod
    def _new_node_setter(node_expr):
        if isinstance(node_expr, jsonpath.Fields):

            def _set_value(target, value):
                for field_name in node_expr.fields:
                    target.value[field_name] = value

            return _set_value

        node_expr_type = ".".join(
            [node_expr.__class__.__module__, node_expr.__class__.__name__]
        )
        raise UnhandledSetter(f"No setter for type {node_expr_type}")

    def _set(self, context, path, value):
        expr = self._get_expr(path)
        if not self.get(context=context, path=path):
            if not expr.left.find(context):
                context = self._set(context, expr.left, {})
            set_value = self._new_node_setter(expr.right)
            for target in expr.left.find(context):
                set_value(target, value)
            return context
        else:
            return expr.update(context, value)

    def set(self, context, path, value):
        return self._set(deepcopy(context), path, deepcopy(value))


def evaluator(_x=None):
    return JSONPath()
