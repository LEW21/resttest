import re

from resttest.http import HTTPResponse


def pipify(func):
    def __ror__(self, other):
        return self(other)

    func.__ror__ = __ror__
    return func


@pipify
class matches:
    def __init__(self, pattern):
        self.pattern = pattern

    def __call__(self, value):
        if isinstance(self.pattern, re.Pattern):
            return self.pattern.fullmatch(value)
        elif isinstance(self.pattern, dict):
            return value is not None and all(value.get(k) | matches(p) for k, p in self.pattern.items())
        elif isinstance(self.pattern, list):
            return value is not None and all(value[k] | matches(p) for k, p in enumerate(self.pattern))
        elif isinstance(self.pattern, HTTPResponse):
            return value.code == self.pattern.code and value.data | matches(self.pattern.data)
        elif callable(self.pattern):
            return self.pattern(value)
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
