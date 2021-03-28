from jsonpath_ng import jsonpath
import re
from .path import evaluator


jsonpath = evaluator()

ANY_TEMPLATE = re.compile(r"{{.*?}}")


def process_template(template, context):
    res = template
    while match := ANY_TEMPLATE.search(res):
        start_res = res
        template_part = match.group()
        re.sub(
            template_part,
            jsonpath.get_one(context=context, path=template_part.strip("{").strip("}")),
        )
        if start_res == res:
            raise ValueError(
                "Templating found patten but changed nothing "
                "likely malformed template or context value"
            )
    return res
