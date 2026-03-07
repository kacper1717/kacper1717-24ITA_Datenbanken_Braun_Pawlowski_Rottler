def _get_int(value, default, *, min_value=None, max_value=None):
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = default
    if min_value is not None and n < min_value:
        n = min_value
    if max_value is not None and n > max_value:
        n = max_value
    return n


def _get_optional_int(value):
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None