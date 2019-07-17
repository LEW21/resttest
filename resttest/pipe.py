import re
from datetime import datetime
from itertools import permutations
from warnings import warn

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
            if value is None:
                return False
            elif isinstance(value, dict):
                return all(value.get(k) | matches(p) for k, p in self.pattern.items())
            else:
                return all(getattr(value, k) | matches(p) for k, p in self.pattern.items())
        elif isinstance(self.pattern, list) or isinstance(self.pattern, tuple):
            if value is None:
                return False
            pattern = self.pattern
            if pattern and pattern[-1] == ...:
               pattern = pattern[:-1]
            else:
                if len(value) != len(self.pattern):
                    warn(f"List length does not match - append ... to the pattern.", UserWarning, 2)
            return all(value[k] | matches(p) for k, p in enumerate(pattern))
        elif isinstance(self.pattern, set):
            if value is None:
                return False
            if len(value) != len(self.pattern):
                return False
            value = list(value)
            for perm in permutations(self.pattern):
                print(perm)
                if value | matches(perm):
                    return True
            return False
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
            if isinstance(value, datetime):
                return value == self.pattern
            else:
                return value == self.pattern.isoformat().replace('+00:00', 'Z')
        else:
            return value == self.pattern

    def __repr__(self):
        return f'matches({repr(self.pattern)})'


@pipify
class not_equal_to:
    pure = True

    def __init__(self, constant):
        self.constant = constant

    def __call__(self, value):
        return value != self.constant

    def __str__(self):
        return f'not equal to <{self.constant}>'
