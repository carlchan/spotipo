from flask import Flask, Blueprint
from flask.helpers import _endpoint_from_view_func



class UnifispotApp(Flask):
    """
    Implementes customizations on Flask
    - Config handler

    """


    def add_unifispot_url_rule(self, rule, endpoint=None,
                            view_func=None, **options):
        if endpoint is None:
            endpoint = _endpoint_from_view_func(view_func)
        if not endpoint.startswith('unifispot.'):
            endpoint = 'unifispot.core.' + endpoint
        self.add_url_rule(rule, endpoint, view_func, **options)


class UnifispotModule(Blueprint):
    "Overwrite blueprint namespace to unifispot.modules.name"

    def __init__(self, name,mtype,*args, **kwargs):
        name = "unifispot.modules." + name
        #used to specify type of module login,prelogin,postlogin or general
        self.mtype = mtype
        super(UnifispotModule, self).__init__(name, *args, **kwargs)
