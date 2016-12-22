import sys
import pytest
from flask import current_app,Flask
from flask_wtf import Form
from wtforms import TextField
from wtforms.validators import Required

from unifispot.core.db import db as _db
from unifispot.utils.modelhelpers import CRUDMixin,SerializerMixin
from unifispot.core.baseviews import RESTView
from tests.helpers import loggin_as_admin

class BaseTestModel(SerializerMixin,CRUDMixin,_db.Model):
    id      = _db.Column(_db.Integer, primary_key=True)
    column1 = _db.Column(_db.String(255))
    column2 = _db.Column(_db.String(10),unique=True)
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


    def get_query(self):
        return BaseTestModel.query


class TestView(RESTView):

    displaycolumns = ['column1','column2']
    def get_modal_obj(self):
        return BaseTestModel()
    def get_form_obj(self):
        return TestForm()        

class TestForm(Form):
    column1 = TextField('Column1',validators=[Required()])
    column2 = TextField('Column2')
    column3 = TextField('Column3')
    column4 = TextField('Column4')

    def populate(self):
        pass

@pytest.fixture(scope='session',autouse=True)
def create_table(db):
    _db.create_all()



def test_get(session,register_testview):  
  
    client = loggin_as_admin()
    resp = client.get("/test/1",follow_redirects=True).json
    assert 'Unknown :TestView ID specified' == resp['msg'],'Unknown ID not \
             giving expected error'
    assert resp['status'] == 0

    testmodel = BaseTestModel(column1='test1',column2='test2',column3='test3',
                          column4='test4')
    testmodel.save()

    resp = client.get("/test/1",follow_redirects=True).json   
    assert resp['status'] == 1
    assert resp['data'] == testmodel.to_dict()   


def test_index(session,register_testview):  

    client = loggin_as_admin()    

    resp = client.get("/test/",follow_redirects=True).json 
    assert resp['recordsTotal'] == '0' ,'Index view not returning proper datatble resp'

    testmodel = BaseTestModel(column1='test1',column2='test2',column3='test3',
                          column4='test4')
    testmodel.save()

    resp = client.get("/test/",follow_redirects=True).json 
    assert resp['recordsTotal'] == '1' ,'Index view not returning proper datatble resp'    

def test_post(session,register_testview):
    client = loggin_as_admin()
    #empty post
    resp = client.post("/test/",follow_redirects=True).json 
    assert resp['status'] == 0
    assert 'Error in the Column1 field - This field is required' in resp['msg'],\
            'Empty form submit is not producing correct error'

    resp = client.post("/test/",follow_redirects=True,\
            data={'column1':'tests','column2':'123'}).json 
    assert resp['status'] == 1
    assert 1 == BaseTestModel.query.count(),'Post failed to create new entry in DB'

    assert '405 METHOD NOT ALLOWED' == client.post("/test/2",
            follow_redirects=True).status,'Post with id is not allowed'
   

def test_put(session,register_testview):
    client = loggin_as_admin()
    #invalid put
    resp = client.put("/test/3",follow_redirects=True).json
    resp['status'] == 0

    assert '405 METHOD NOT ALLOWED' == client.put("/test/",
            follow_redirects=True).status
    
    testmodel = BaseTestModel(column1='test1',column2='test2',column3='test3',
                          column4='test4')
    testmodel.save()

    resp = client.put("/test/1",follow_redirects=True,\
            data={'column1':'tests','column4':'123'}).json 
    assert resp['status'] == 1
    assert 1 == BaseTestModel.query.count(),'Put failed to update entry'

    assert 'tests' == BaseTestModel.query.get(1).column1,'Put failed to update entry'

def test_delete(session,register_testview):
    client = loggin_as_admin()

    assert '405 METHOD NOT ALLOWED' == client.delete("/test/",
            follow_redirects=True).status
    
    testmodel = BaseTestModel(column1='test1',column2='test2',column3='test3',
                          column4='test4')
    testmodel.save()

    resp = client.delete("/test/1",follow_redirects=True,).json 
    assert resp['status'] == 1
    assert 0 == BaseTestModel.query.count(),'Delete failed to delete entry'
