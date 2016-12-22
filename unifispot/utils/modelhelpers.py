from flask import Blueprint,current_app
from flask.json import JSONEncoder as BaseJSONEncoder
import arrow
from flask_babelex import format_datetime as _format_datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.properties import ColumnProperty
from unifispot.core.db import db


class JSONEncoder(BaseJSONEncoder):
    """Custom :class:`JSONEncoder` which respects objects that include the
    :class:`JsonSerializer` mixin.

        Based on https://raw.githubusercontent.com/mattupstate/overholt/master/overholt/helpers.py
    """
    def default(self, obj):
        if isinstance(obj, SerializerMixin):
            return obj.to_json()
        return super(JSONEncoder, self).default(obj)


class SerializerMixin(object):
    """A mixin that can be used to mark a SQLAlchemy model class which
    implements a :func:`to_dict` method.  By default this
    mixin will assume all properties of the SQLAlchemy model are to be visible
    in the JSON output. Extend this class to customize which properties are
    public, hidden or modified before being being passed to the JSON serializer.

    Modifier can be a method of the current object, or the name of a method

    

        Based on https://raw.githubusercontent.com/mattupstate/overholt/master/overholt/helpers.py
    """

    __json_public__ = None
    __json_hidden__ = None
    __json_modifiers__ = None

    def get_field_names(self):
        fields = []
        for p in self.__mapper__.iterate_properties:
            #only serialize columns
            if  type(p) == ColumnProperty:
                fields.append(p.key)
        return fields

    def format_datetime(self,key):
        return { key: _format_datetime(getattr(self, key)) }

    def to_dict(self):
        field_names = self.get_field_names()

        public = self.__json_public__ or field_names
        hidden = self.__json_hidden__ or []
        modifiers = self.__json_modifiers__ or dict()

        rv = dict()
        for key in public:
            if key in hidden:
                continue
            rv[key] = getattr(self, key)
        for key, modifier in modifiers.items():
            value = getattr(self, key)
            if isinstance(modifier, basestring):
                modifier = getattr(self,modifier)
                rv.update(modifier(key))
            else:
                rv.update(modifier(self,key))
        return rv

class ExportMixin(object):
    ''' Mixin to be used for creating CSV export,similar to SerialMixin

    '''

    __export_public__ = None
    __export_hidden__ = None
    __export_modifiers__ = None
    __export_titles__ = None

    def get_field_names(self):
        fields = []
        for p in self.__mapper__.iterate_properties:
            #only serialize columns
            if  type(p) == ColumnProperty:
                fields.append(p.key)
        return fields

    def get_titles(self):
        return self.__export_titles__ or self.__export_public__ 
        
    def format_datetime(self,key):
        return { key: _format_datetime(getattr(self, key)) }

    def to_row(self):
        field_names = self.get_field_names()

        public = self.__export_public__ or field_names
        hidden = self.__export_hidden__ or []
        modifiers = self.__export_modifiers__ or dict()

        rv = dict()
        for key in public:
            if key in hidden:
                continue
            rv[key] = getattr(self, key)
        for key, modifier in modifiers.items():
            value = getattr(self, key)
            if isinstance(modifier, basestring):
                modifier = getattr(self,modifier)
                rv.update(modifier(key))
            else:
                rv.update(modifier(self,key))
        return rv



class CRUDMixin(object):
    """A mixin that provides basic CRUD (Create Read Update and Delete ) functionality for a model

        Based on CRUD implementation from flaskage (flaskage.readthedocs.io)
    """    
    __table_args__ = {'extend_existing': True}

    __form_fields_avoid__     = ['id']
    __form_fields_modifiers__ = None

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        return instance.save()

    def update(self, commit=True, **kwargs):
        for attr, value in kwargs.iteritems():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        try:
            db.session.add(self)
            if commit:
                db.session.commit()
        except SQLAlchemyError as exception:
            db.session.rollback()
            raise exception
        return self

    def delete(self, commit=True):
        try:
            db.session.delete(self)
            if commit:
                db.session.commit()
        except SQLAlchemyError as exception:
            db.session.rollback()
            raise exception
        return 1


    def get_field_names(self):
        fields = []
        for p in self.__mapper__.iterate_properties:
            #only serialize columns
            if  type(p) == ColumnProperty:
                fields.append(p.key)
        return fields

    def populate_from_dict(self,dict):
        for attr,value in dict.iteritems():
            setattr(self, attr, value)
        return self.save() or self            


    def populate_from_form(self,form):
        field_names = self.get_field_names()
        avoid = self.__form_fields_avoid__ or []
        modifiers = self.__form_fields_modifiers__ or dict()

        for field_name in field_names:
            if  field_name in avoid:
                continue
            modifier = modifiers.get(field_name)
            if modifier:
                if isinstance(modifier, basestring):
                    modifier = getattr(self,modifier)
                    value = modifier(form,field_name)
                else:
                    value = modifier(self,form,field_name)  
            else:
                value = getattr(form,field_name).data              
            setattr(self, field_name,value )
        return self.save() or self

    ##------------special methods to handle JSON type data starts
    #special methods for using a Text JSON field in model to start arbitery config
    #Each field in model maps to a number of form fields
    #Model field should be named as constant_xxxx
    #Form field should be named as constant_xxxx1,constant_xxxx2 etc
    def modeljson_to_dict(self,field_name):
        #add dictionary stored in the field_name to JSON
        return getattr(self,field_name) or {}       



    def form_to_modeljson(self,form,field_name):
        #special function to convert method fields to
        #correspending db column
        method_field = {}
        prefix = str(field_name).split('_')[0]
        for formfield, value in form.data.items():
            if formfield.startswith(prefix):        
                if getattr(form,formfield).type == 'BooleanField':
                    #serialize boolean check boxes
                    value = 1 if value else 0
                method_field[formfield] = value      
        return method_field     
    ##------------special methods to handle JSON type data ends   