# coding: utf-8
import os
import importlib
import logging

logger = logging.getLogger()


def load_from_folder(app):
    """
        This code looks for any modules or packages in the given
        directory, loads them
        and then registers a blueprint
        - blueprints must be created with the name 'module'
        Implemented directory scan

        Bulk of the code taken from:
            https://github.com/quokkaproject/quokka/tree/development/quokka
    """
    blueprints_path = app.config.get('MODULE_PATH', 'modules')
    path = os.path.join(
        app.config.get('PROJECT_ROOT', '..'),
        blueprints_path
    )
    base_module_name = ".".join([app.name, blueprints_path])
    dir_list = os.listdir(path)
    mods = {}
    object_name     = app.config.get('BLUEPRINTS_OBJECT_NAME', 'module')
    module_file     = app.config.get('BLUEPRINTS_MODULE_NAME', 'main')
    settings_file   = app.config.get('BLUEPRINTS_SETTINGS_NAME', 'settings')
    settings_module = settings_file + '.py'
    blueprint_module= module_file + '.py'
    for fname in dir_list:
        if not os.path.exists(os.path.join(path, fname, 'DISABLED')) and  \
                os.path.isdir(os.path.join(path, fname)) and \
                os.path.exists(os.path.join(path, fname, blueprint_module)):


            # register blueprint object
            module_root = ".".join([base_module_name, fname])
            module_name = ".".join([module_root, module_file])

            #load blueprint settings if exists
            if os.path.exists(os.path.join(path, fname, settings_module)):
                app.config.from_object(".".join([module_root, settings_file]))

            mods[fname] = importlib.import_module(module_name)
            blueprint = getattr(mods[fname], object_name)
            #logger.info("registering blueprint: %s" % blueprint.name)
            url_prefix = app.config.get(fname.upper() + '_URL_PREFIX','')
            app.register_blueprint(blueprint,url_prefix=url_prefix)

            #find and register login methods
            if blueprint.mtype == 'login':
                logger.info("registering loginmethod: %s" % fname)
                app.config['GUESTLOGIN_MODULES'].append(fname)

            #load all celery tasks


    logger.info("%s modules loaded", mods.keys())
    logger.info("%s login modules loaded", app.config['GUESTLOGIN_MODULES'])


