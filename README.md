# Workflows test client

A POC for a workflows test client, example in scratch, workflow was build with `flows_as_functions` branch.
This is very much a WIP/POC and needs a lot of work before it should be used

Example can be ran using:

```shell
PYTHONPATH="." ipython -i ./example.py
```

## Notes

- set_task_breakpoint allows you to return a task which would otherwise not be returned

## TODO

- [ ] Clean up stack handling
- [ ] Implement all workflow task/components/validators
- [ ] Check it conforms with docs
- [ ] TESTS!!!!
- [ ] CI
- [ ] Packaging
- [ ] Docs
