import json


class Renderer:
    def __init__(self, title, output_file):
        self.out = open(output_file, 'w')
        self.print(f'# {title}')

    def print(self, *args, **kwargs):
        print(*args, **kwargs, file = self.out)

    def start_file(self, name):
        self.print(f"# {name}")

    def start_case(self, name):
        self.print()
        self.print(f'## {name}')

    def write_text(self, text):
        self.print()
        self.print(text)

    def write_var(self, var, desc):
        return
        self.print()
        self.print(f'* `{var}`: {desc}')

    def _write_value(self, data, level = 0, newline_required = False):
        if isinstance(data, dict) and data:
            self._write_dict(data, level, newline_required)
        elif isinstance(data, list) and data:
            self._write_list(data, level - 1, newline_required)
        else:
            self.print(self._dump(data))

    def _write_dict(self, data, level = 0, newline_required = False):
        if newline_required:
            self.print()
        for k, v in data.items():
            if newline_required:
                self.print('  ' * level, end = '')
            else:
                newline_required = True
            self.print(f'{k}: ', end = '')
            self._write_value(v, level + 1, newline_required = True)

    def _write_list(self, data, level = 0, newline_required = False):
        self.print()
        for v in data:
            self.print('  ' * level + f'- ', end = '')
            self._write_value(v, level + 1)

    def _string(self, value):
        if isinstance(value, str):
            return value
        else:
            return f'<{value}>'

    def _dump(self, value):
        try:
            return json.dumps(value)
        except:
            return f'<{value}>'

    def write_http_message(self, status_line, data):
        self.print()
        self.print('```http')
        self.print(status_line)
        if data:
            self.print()
            self._write_value(data)

        self.print('```')

    def write_http_request(self, method, url, data):
        self.write_http_message(f'{method} {self._string(url)}', data)

    def write_http_response(self, response):
        self.write_http_message(f'{response.code} {response.reason}', response.data)

    def write_object(self, object):
        schema = object.__resttest_schema__
        self.start_case(f'The {schema.title} object')
        self.print(getattr(schema, 'description', ''))
        self.print()

        self.print('### Properties')
        self.print('Name | Type | Description')
        self.print('- | - | -')
        for prop_name, prop_schema in schema.properties.items():
            prop_type = get_nice_type(prop_schema)
            self.print(f'{prop_name} | {prop_type} | {getattr(prop_schema, "description", "")}')


def get_nice_type(schema):
    undefined = object()

    ref = getattr(schema, '$ref', undefined)
    if ref is not undefined:
        assert ref.startswith('#/definitions/')
        def_name = ref[len('#/definitions/'):]
        return def_name

    const = getattr(schema, 'const', undefined)
    if const is not undefined:
        return json.dumps(const)

    anyOf = getattr(schema, 'anyOf', undefined)
    if anyOf is not undefined:
        return ' or '.join(get_nice_type(subschema) for subschema in anyOf)

    title = getattr(schema, 'title', undefined)
    if title is not undefined:
        return title

    format = getattr(schema, 'format', undefined)
    if format is not undefined:
        return format

    type = getattr(schema, 'type', '')
    if type == 'array':
        return f'array&lt;{get_nice_type(schema.items)}&gt;'

    return type
