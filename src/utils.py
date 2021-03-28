def deepmerge(*dicts):
    result = dicts[0]
    for d in dicts[1:]:
        for key, value in d.items():
            current = result.get(key, None)
            if isinstance(current, dict):
                result[key] = deepmerge(current, value)
            else:
                result[key] = value
    return result
