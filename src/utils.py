from copy import deepcopy


def _deepmerge(*dicts: dict) -> dict:
    result = dicts[0]
    for d in dicts[1:]:
        for key, value in d.items():
            current = result.get(key, None)
            if isinstance(current, dict):
                result[key] = _deepmerge(current, value)
            else:
                result[key] = value
    return result


def deepmerge(*dicts: dict) -> dict:
    """Returns a merge of the nested dicts with the
    later dict overwritting the newer
    ```
    >>> A = {"x": 1, "z": 4}
    >>> A = {"x": 2, "y": 3}
    >>> merge_stat(A, B)
    {"x": 2, "y": 3, "z": 4}


    """
    return _deepmerge(*map(deepcopy, dicts))


def _deepdiff(a: dict, b: dict) -> dict:
    result = {}
    for key, value_a in a.items():
        if key not in b:
            result[key] = value_a
        elif isinstance(value_a, dict) and isinstance(value_b := b[key], dict):
            if inner_diff := _deepdiff(value_a, value_b):
                result[key] = inner_diff
        elif value_a != b[key]:
            result[key] = value_a
    return result


def deepdiff(a: dict, b: dict) -> dict:
    """
    returns new values and updates to existing values in A relative to B
    and values which are present in B but not in A are dropped e.g.:
    ```
    >>> A = {"x": 1, "y": 3, "z": 4}
    >>> B = {"x": 2, "y": 3, "w": 5}
    >>> diff_strat(A, B)
    {"x": 1, "z": 4}
    ```
    """
    return _deepmerge(deepcopy(a), deepcopy(b))
