from flask import g,current_app
from babel.support import LazyProxy
from flask_babelex import gettext, lazy_gettext, ngettext
from flask_babelex import format_datetime as _format_datetime


def ugettext(s):
    # we assume a before_request function
    # assigns the correct user-specific
    # translations
    return g.translations.ugettext(s)

ugettext_lazy = LazyProxy(ugettext)

_ = gettext
_l = lazy_gettext
_n = ngettext

def format_datetime(dtime):
    with current_app.app_context():
        return _format_datetime(dtime)
