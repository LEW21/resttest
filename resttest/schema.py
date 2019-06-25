from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence, Union
from warnings import warn

from pkg_resources import resource_string
from typing_extensions import Literal
from yaml import safe_load

ALWAYS_DICTS = {'definitions', 'properties'}


def make_schemaless_object(data, always_dicts = set(), key = None):
    if isinstance(data, dict):
        processed_data = {k: make_schemaless_object(v, always_dicts, k) for k, v in data.items()}
        return SchemalessObject(processed_data) if key not in always_dicts else processed_data
    elif isinstance(data, list):
        return [make_schemaless_object(v, always_dicts) for v in data]
    else:
        return data


class SchemalessObject:
    def __init__(self, data):
        self._data = data

    def __getattr__(self, attr):
        try:
            return self._data[attr]
        except KeyError as e:
            raise AttributeError(attr) from e

    def __str__(self):
        return str(self._data)


class Undefined:
    def __repr__(self):
        return 'undefined'


class SchemaDocument:
    def __init__(self, schema: Schema):
        self.document = schema
        if isinstance(self.document.definitions, SchemalessObject):
            self.document.definitions = self.document.definitions._data

    def to_type(self, schema: Schema, override_type = None):
        assert not isinstance(schema, dict)
        undefined = Undefined()

        ref = getattr(schema, '$ref', undefined)
        if ref is not undefined:
            if ref == '#':
                # TODO Recursion
                return Any

            assert ref.startswith('#/definitions/')
            def_name = ref[len('#/definitions/'):]
            return self.to_type(self.document.definitions[def_name])

        if schema == True:
            return Any

        const = getattr(schema, 'const', undefined)
        if const is not undefined:
            if const is None:
                return type(None)
            else:
                return Literal[const]

        anyOf = getattr(schema, 'anyOf', undefined)
        if anyOf is not undefined:
            return Union[tuple(self.to_type(subschema) for subschema in anyOf)]

        schema_type = override_type or getattr(schema, 'type', undefined)

        if isinstance(schema_type, list):
            return Union[tuple(self.to_type(schema, override_type = single_type) for single_type in schema_type)]

        if schema_type == 'null':
            return type(None)
        if schema_type == 'boolean':
            return bool
        if schema_type == 'integer':
            return int
        if schema_type == 'number':
            return float
        if schema_type == 'string':
            format = getattr(schema, 'format', None)
            if format == 'date-time':
                return datetime
            return str

        if schema_type == 'object':
            properties = getattr(schema, 'properties', undefined)
            additionalProperties = getattr(schema, 'additionalProperties', undefined)

            if properties is not undefined and additionalProperties is not undefined:
                raise NotImplementedError('Handling both properties and additionalProperties on a single object is not implemented.')

            if properties is not undefined:
                if isinstance(properties, SchemalessObject):
                    properties = properties._data
                property_types = dict()
                default_values = dict()
                for prop_name, prop_schema in properties.items():
                    property_types[prop_name] = self.to_type(prop_schema)
                    default = getattr(prop_schema, 'default', undefined)
                    if default is not undefined:
                        default_values[prop_name] = default

                def __init__(self, **kwargs):
                    unknown_kwargs = set(kwargs.keys()) - set(type(self).__annotations__.keys())
                    if unknown_kwargs != set():
                        raise TypeError(f'{type(self).__name__} got unexpected properties: {", ".join(unknown_kwargs)}')

                    for prop_name, prop_type in type(self).__annotations__.items():
                        if prop_name in kwargs:
                            setattr(self, prop_name, kwargs[prop_name])

                def __str__(self):
                    return f'{type(self).__name__} {self.__dict__}'

                Patch = type((schema.title or '') + 'Patch', (), dict(
                    __annotations__ = property_types,
                    __resttest_plain__ = True,
                    __resttest_schema__ = schema,
                    __init__ = __init__,
                    __str__ = __str__,
                    __repr__ = __str__,
                ))

                Full = type(schema.title or '', (Patch,), dict(
                    Patch = Patch,
                    **default_values,
                ))

                def __init__(self, **kwargs):
                    missing_kwargs = set(type(self).__annotations__.keys()) - set(kwargs.keys()) - set(type(self).__dict__.keys())
                    if missing_kwargs != set():
                        raise TypeError(f'{type(self).__name__} missing required properties: {", ".join(missing_kwargs)}')

                    super(Full, self).__init__(**kwargs)

                Full.__init__ = __init__

                return Full

            if additionalProperties is not undefined:
                return Mapping[str, self.to_type(additionalProperties)]

            warn(f"Untyped object: {schema}", UserWarning, 2)
            return dict

        if schema_type == 'array':
            items = getattr(schema, 'items', undefined)

            if items is not undefined:
                if isinstance(items, list):
                    raise NotImplementedError('Handling pre-set list items is not implemented.')

                return Sequence[self.to_type(items)]

            warn(f"Untyped array: {schema}", UserWarning, 2)
            return list

        warn(f"Untyped value: {schema}", UserWarning, 2)
        return Any


def schema_to_type(top_level_schema: Schema, chosen_schema: Schema = None):
    return SchemaDocument(top_level_schema).to_type(chosen_schema or top_level_schema)


Schema = schema_to_type(make_schemaless_object(safe_load(resource_string(__name__, 'schema.yaml'))))


def unserialize(Object, data):
    if Object == Schema:
        # TODO delete after this becomes strong enough to interpret JSON Schema schema correctly
        return make_schemaless_object(data, ALWAYS_DICTS)

    if Object == type(None):
        if data is not None:
            raise ValueError(Object)
        return data

    if getattr(Object, '__origin__', None) == Literal:
        const = Object.__args__[0]
        if data != const:
            raise ValueError(Object)
        return data

    if Object == bool:
        if not isinstance(data, bool):
            raise ValueError(Object)
        return data

    if Object == int:
        if not isinstance(data, int):
            raise ValueError(Object)
        return data

    if Object == float:
        if not isinstance(data, float):
            raise ValueError(Object)
        return data

    if Object == str:
        if not isinstance(data, str):
            raise ValueError(Object)
        return data

    if Object == datetime:
        if not isinstance(data, str):
            raise ValueError(Object)
        if not data.endswith('Z'):
            raise NotImplementedError('Parsing dates with non-Z timezones is not supported.')
        return datetime.fromisoformat(data[:-1]).replace(tzinfo = timezone.utc)

    if getattr(Object, '__resttest_plain__', False):
        if not isinstance(data, dict):
            raise ValueError(Object)

        unknown_data = set(data.keys()) - set(Object.__annotations__.keys())
        if unknown_data != set():
            warn(f'{Object.__name__} has unknown properties: {", ".join(unknown_data)}', UserWarning, 2)

        missing_data = set(Object.__annotations__.keys()) - set(data.keys()) - set(Object.__dict__.keys())
        if missing_data != set():
            raise TypeError(f'{Object.__name__} is missing required properties: {", ".join(missing_data)}')

        kwargs = dict()
        for prop_name, prop_type in Object.__annotations__.items():
            if prop_name in data:
                kwargs[prop_name] = unserialize(prop_type, data[prop_name])

        return Object(**kwargs)

    if getattr(Object, '__origin__', None) == Union:
        results = []

        for arg in Object.__args__:
            try:
                results.append(unserialize(arg, data))
            except ValueError as e:
                pass

        if len(results) > 1:
            raise NotImplementedError('Matching multiple options from anyOf is not implemented.')

        if len(results) == 1:
            return results[0]

        raise ValueError(Object)

    if Object == dict:
        if not isinstance(data, dict):
            raise ValueError(Object)
        return data

    if issubclass(getattr(Object, '__origin__', type(None)), Sequence):
        if not isinstance(data, list):
            raise ValueError(Object)
        item_type = Object.__args__[0]
        return [unserialize(item_type, item) for item in data]

    if Object == list:
        if not isinstance(data, list):
            raise ValueError(Object)
        return data

    if Object == Any:
        return data

    raise ValueError(Object)
