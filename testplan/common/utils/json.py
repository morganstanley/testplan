import json

_USE_RAPIDJSON = False

try:
    import rapidjson
except ImportError:
    pass
else:
    _USE_RAPIDJSON = True


def json_loads(data: str):
    if _USE_RAPIDJSON:
        # being explicit here
        return rapidjson.loads(data, number_mode=rapidjson.NM_NAN)
    else:
        return json.loads(data)


def json_dumps(data, indent_2=False, default=None) -> str:
    if _USE_RAPIDJSON:
        # being explicit here
        return rapidjson.dumps(
            data,
            indent=2 if indent_2 else None,
            default=default,
            number_mode=rapidjson.NM_NAN,
        )
    else:
        if default:

            class _E(json.JSONEncoder):
                def default(self, o):
                    return default(o)

        else:
            _E = None
        return json.dumps(data, cls=_E, indent=2 if indent_2 else None)
