workflow_str = """
    {
        "validators": {
            "not_zero_length": {
                "type": "isLength",
                "message": {
                    "type": "error",
                    "template": "Field can not be empty"
                },
                "valid_when": true,
                "validator_value": 1
            },
            "should_save_message": {
                "type": "equals",
                "message": {
                    "type": "error",
                    "template": "Error: equals to values"
                },
                "valid_when": true,
                "value_key": "$.save",
                "validator_value": true
            }
        },
        "components": {
            "input_Input message here": {
                "type": "input",
                "label": "Input message here",
                "validator": [
                    "not_zero_length"
                ]
            },
            "submit_button": {
                "type": "button",
                "action": "submit",
                "style": "primary",
                "text": "Submit"
            },
            "HelloWorldMessage": {
                "type": "message_box",
                "message": {
                    "template": "{{$.message}}",
                    "type": "info"
                },
                "size": null
            },
            "back_button": {
                "type": "button",
                "action": "back",
                "style": "primary",
                "text": "Back"
            },
            "next_button_next_primary_reset_save_false_buttons": {
                "type": "button",
                "action": "next",
                "style": "primary",
                "text": "Reset",
                "value": false
            },
            "next_button_next_primary_save_message_save_true_buttons": {
                "type": "button",
                "action": "next",
                "style": "primary",
                "text": "Save Message",
                "value": true
            }
        },
        "flows": {
            "QuickWorkflow": {
                "tasks": [
                    {
                        "type": "screen",
                        "name": "InputMessage",
                        "components": [
                            [
                                {
                                    "name": "input_Input message here",
                                    "destination_path": "$.message"
                                }
                            ],
                            [
                                {
                                    "name": "submit_button"
                                }
                            ]
                        ]
                    },
                    {
                        "type": "screen",
                        "name": "DisplayMessage",
                        "components": [
                            [
                                {
                                    "name": "HelloWorldMessage"
                                }
                            ],
                            [
                                {
                                    "name": "next_button_next_primary_reset_save_false_buttons",
                                    "destination_path": "$.save"
                                }
                            ],
                            [
                                {
                                    "name": "back_button"
                                }
                            ],
                            [
                                {
                                    "name": "next_button_next_primary_save_message_save_true_buttons",
                                    "destination_path": "$.save"
                                }
                            ]
                        ]
                    },
                    {
                        "type": "jsonrpc",
                        "name": "SaveMessage",
                        "preconditions": [
                            "should_save_message"
                        ],
                        "url": "/api/save",
                        "method": null,
                        "payload_paths": [
                            {
                                "key": "$.message",
                                "result_key": "$.message_to_save"
                            }
                        ],
                        "payload": {
                            "message_to_save": null,
                            "token": "RequestToken!"
                        }
                    },
                    {
                        "type": "redirect",
                        "name": "Restart",
                        "url": "/api/quickstart"
                    }
                ],
                "config": {}
            }
        },
        "starting_flow": "QuickWorkflow",
        "hash": "ee6c8685802a96d12ea474d97ad26c252fb3739be2e8a0c2fcfd2a9f8beb9eff10a7ae22cd7cc8d61d1f14c2f624629b6c6284b25853f76fccf28a01469789d8",
        "context": {}
    }"""


from src.client import TestClient
from src.server import MockServer, Methods

workflow_url = "/api/quickstart"


s = MockServer()
s.register_handler(workflow_url, Methods.GET, lambda _: workflow_str)

w = TestClient(s, workflow_url)
t = w.get_task()
t_old = t
t = w.get_task()
assert t == t_old
print(t.get_components())
t.click("submit_button")
t_old = t
t = w.get_task()
assert t == t_old
t.set("input_Input message here", "Hello :)")
t.click("submit_button")
t_old = t
t = w.get_task()
assert t != t_old
t_back_target = t_old
t.click("back_button")
t_old = t
t = w.get_task()
assert t != t_old
assert t == t_back_target
t.set("input_Input message here", "Hello :)")
t.click("submit_button")
t_old = t
t = w.get_task()
assert t != t_old
t.click("next_button_next_primary_save_message_save_true_buttons")
w.set_task_breakpoint("Restart")  # Grab redirect which should be next
t_old = t
t = w.get_task()
assert t != t_old
assert t.task_type == "redirect"
t_old = t
t = w.get_task()  # Reload flow
assert t != t_old
assert t.name == "InputMessage"
