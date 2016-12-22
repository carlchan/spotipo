import sys
import pytest
from flask import current_app
from flask_wtf import Form
from wtforms import TextField

from unifispot.core.db import db as _db
from unifispot.utils.modelhelpers import CRUDMixin,SerializerMixin

class TestModel(SerializerMixin,CRUDMixin,_db.Model):
    id      = _db.Column(_db.Integer, primary_key=True)
    column1 = _db.Column(_db.String(255))
    column2 = _db.Column(_db.String(255))
    column3 = _db.Column(_db.String(255))
    column4 = _db.Column(_db.String(255))

    def test_mod_form(self,form,data):
        return 'random'

    def test_mod_dict(self,key):
        return {key:'random'}

    __form_fields_modifiers__   = {'column2':test_mod_form, 'column4':'test_mod_form'}
    __form_fields_avoid__       = ['id','column3']

    __json_hidden__             = ['column1']
    __json_modifiers__          = {'column3':test_mod_dict, 'column4':'test_mod_dict'} 

class TestForm(Form):
    column1 = TextField('Column1')
    column2 = TextField('Column2')
    column3 = TextField('Column3')
    column4 = TextField('Column4')

@pytest.fixture(scope='session',autouse=True)
def create_table(db):
    _db.create_all()

@pytest.fixture(scope='function',autouse=True)
def populate_modelmixin(db,session,create_table):
    _db.create_all()

    testmodel = TestModel(column1="test1",column2="test2",
                          column3="test3",column4="test4")    
    session.add(testmodel)
    session.commit()


def test_create(populate_modelmixin,session):
    TestModel.create(column1='test1',column2='test2')
    assert TestModel.query.count() == 2, 'Entry not added to DB'

def test_update(populate_modelmixin,session):
    testmodel = TestModel.query.get(1)
    testmodel.update(column1='magic1')

    assert TestModel.query.filter_by(id=1).first().column1 == 'magic1', \
            'Entry Updation not working'

def test_save(populate_modelmixin,session):
    testmodel = TestModel(column1="test1",column2="test2",
                          column3="test3") 
    testmodel.save()
    assert TestModel.query.count() == 2, 'Entry not added to DB'    


def test_delete(populate_modelmixin,session):
    testmodel = TestModel.query.get(1)
    testmodel.delete()
    assert TestModel.query.count() == 0, 'Entry not deleted'    

def test_populate_from_form(populate_modelmixin,session,request):
    testmodel = TestModel.query.get(1)
    with current_app.test_request_context():
        testform  = TestForm()
        testform.column1.data = 'newmagic1'
        testform.column2.data = 'newmagic2'
        testform.column3.data = 'newmagic3'
        testform.column4.data = 'newmagic4'
        testmodel.populate_from_form(testform)

    newtestmodel = TestModel.query.get(1)

    assert newtestmodel.column1 == 'newmagic1', 'populate from form failed'
    assert newtestmodel.column2 == 'random', 'modifier not working'
    assert newtestmodel.column3 == 'test3', 'avoid not working'
    assert newtestmodel.column4 == 'random', 'modifier via method_name not working'

def test_to_dict1(populate_modelmixin,session):
    testmodel = TestModel.query.get(1)

    assert {'column2':'test2','column3':'random','column4':'random',
                'id':1} == testmodel.to_dict()
                        

