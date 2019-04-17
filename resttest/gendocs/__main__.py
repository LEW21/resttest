import importlib
import pkgutil

import resttest
from resttest.gendocs.generator import render_module

resttest.BASE_URL = '/'

for module in pkgutil.iter_modules(['tests']):
    if not module.name.startswith('test_'):
        continue

    try:
        mod = importlib.import_module('tests.' + module.name)
    except ImportError as e:
        print(f'{module.name}: {e}')
    else:
        if hasattr(mod, 'resttest'):
            render_module(mod)
