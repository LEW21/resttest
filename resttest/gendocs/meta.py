import collections.abc
import typing
from datetime import timedelta


class Dummy:
    def dummy(self):
        pass


BoundMethod = type(Dummy().dummy)


def property_type(cls, name):
    try:
        return typing.get_type_hints(cls)[name]
    except KeyError:
        static_property = getattr(cls, name)

        if isinstance(static_property, property):
            return typing.get_type_hints(static_property.fget).get('return')

        if callable(static_property):
            return BoundMethod

    raise AttributeError(name)


def return_type(callable):
    try:
        return typing.get_type_hints(callable)['return']
    except KeyError:
        if isinstance(callable, type):
            return callable

    return None


PURE_FUNCTIONS = {
    list,
    set,
    dict,
    timedelta,
}


def is_pure(callable):
    return callable in PURE_FUNCTIONS or getattr(callable, 'pure', False) == True


class BoundProperty:
    def __init__(self, attr, obj):
        self.__self__ = obj
        self.__attr__ = attr
        self.var_name = None

    def __getattr__(self, attr):
        return BoundProperty(attr, self)

    def __str__(self):
        if self.var_name:
            return self.var_name
        return f'{self.__self__}.{self.__attr__}'


class Instance:
    def __init__(self, of, doc = None):
        self.of = of
        self.__doc__ = doc
        self.var_name = None

    def __getattr__(self, attr):
        try:
            type = property_type(self.of, attr)
        except AttributeError:
            pass
        else:
            if type == BoundMethod:
                return BoundMethod(getattr(self.of, attr), self)

            return make_instance(type)

        return BoundProperty(attr, self)

    def __str__(self):
        if self.var_name:
            return self.var_name
        else:
            try:
                return f'<{self.of.__module__}.{self.of.__qualname__} instance>'
            except AttributeError:
                if self.of.__module__ == 'typing':
                    return f'<{str(self.of)} instance>'
                raise

    def __add__(self, other):
        return Instance(self.of)

    def __sub__(self, other):
        return Instance(self.of)


class IterableInstance(Instance):
    def __init__(self, of, doc = None):
        super().__init__(of, doc)

    def __iter__(self):
        while True:
            yield make_instance(self.of.__args__[0])


def make_instance(of = None, doc = None):
    if of == None:
        of = object

    if getattr(of, '__origin__', None) == collections.abc.Iterable:
        return IterableInstance(of, doc)

    return Instance(of, doc)


def class_of(v):
    if isinstance(v, Instance):
        return v.of
    else:
        return v.__class__


def is_instance_of(v, t):
    return isinstance(v, t) or (isinstance(v, Instance) and v.of == t)
