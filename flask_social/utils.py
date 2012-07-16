
from importlib import import_module

from flask import current_app, flash


def do_flash(message, category):
    if config_value('FLASH_MESSAGES'):
        flash(message, category)


def get_class_from_string(clazz_name):
    """Get a reference to a class by its configuration key name."""
    cv = clazz_name.split('::')
    cm = import_module(cv[0])
    return getattr(cm, cv[1])


def config_value(key, app=None):
    app = app or current_app
    return app.config['SOCIAL_' + key.upper()]
