"""Application errors that map to HTTP responses."""


class AppError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def _as_int(value, name):
    if isinstance(value, bool) or value is None:
        raise AppError(f"Invalid {name}.")
    if isinstance(value, float) and not value.is_integer():
        raise AppError(f"Invalid {name}.")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise AppError(f"Invalid {name}.") from exc


def parse_positive_int(value, name="quantity"):
    number = _as_int(value, name)
    if number <= 0:
        raise AppError(f"Invalid {name}.")
    return number


def parse_non_negative_int(value, name="quantity"):
    number = _as_int(value, name)
    if number < 0:
        raise AppError(f"Invalid {name}.")
    return number
