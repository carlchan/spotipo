# -*- coding: utf-8 -*-

from flask import session, current_app
from  flask_themes2 import render_theme_template,get_theme,get_themes_list


def render_template(template, **context):
    theme = session.get('theme', current_app.config['DEFAULT_THEME'])
    return render_theme_template(theme, template, _fallback=False, **context )


def render_dt_buttons(row):
    '''Create Edit and Delete buttons in datatable corresponding to the ID

    '''
    return '''<a class="btn btn-red btn-sm delete" href="#" id="%s" alt="Delete">
                   <i class="fa fa-times"></i>Delete</a>
            <a class="btn  btn-sm edit" href="#" id="%s" alt="Edit">
                        <i class="fa fa-pencil"></i>Edit</a>'''%(row.id,row.id)
