import re
from datetime import datetime

from resttest.http import HTTPResponse


def pipify(func):
    def __ror__(self, other):
        return self(other)

    func.__ror__ = __ror__
    return func


undefined = object()


@pipify
class matches:
    def __init__(self, pattern = undefined, **kwargs):
        self.pattern = pattern if pattern is not undefined else kwargs

    def __call__(self, value):
        if isinstance(self.pattern, re.Pattern):
            return self.pattern.fullmatch(value)
        elif isinstance(self.pattern, dict):
            return value is not None and all(value.get(k) | matches(p) for k, p in self.pattern.items())
        elif isinstance(self.pattern, list):
            return value is not None and all(value[k] | matches(p) for k, p in enumerate(self.pattern))
        elif isinstance(self.pattern, HTTPResponse):
            return value.code == self.pattern.code and value.data | matches(self.pattern.data)
        elif isinstance(self.pattern, type):
            try:
                self.pattern(value)
            except ValueError:
                return False
            else:
                return True
        elif callable(self.pattern):
            return self.pattern(value)
        elif isinstance(self.pattern, datetime):
            return value == self.pattern.isoformat().replace('+00:00', 'Z')
        else:
            return value == self.pattern


@pipify
class not_equal_to:
    pure = True

    def __init__(self, constant):
        self.constant = constant

    def __call__(self, value):
        return value != self.constant

    def __str__(self):
        return f'not equal to <{self.constant}>'
