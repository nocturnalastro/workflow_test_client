from collections import namedtuple
import json


ParseResult = namedtuple(
    "ParseResult",
    ("components", "validators", "flows", "starting_flow", "context"),
)


class InvalidWorkflow(Exception):
    pass


def json_parser(workflow_str) -> ParseResult:
    try:
        wf = json.loads(workflow_str)
        return ParseResult(
            components=wf["components"],
            validators=wf["validators"],
            flows=wf["flows"],
            starting_flow=wf["starting_flow"],
            context=wf["context"],
        )

    except Exception as e:
        raise InvalidWorkflow from e
