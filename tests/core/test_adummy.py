import sys
import pytest
from flask import current_app
from flask_wtf import Form
from wtforms import TextField
from faker import Faker
import arrow
import uuid



def test_dummy1(register_testview,register_testvalidateview):
    #just a dummy test to initialize all fixtures that need to be executed 
    #before first request
    pass


def test_dummy2(register_testredirectguest):
    #just a dummy test to initialize all fixtures that need to be executed 
    #before first request
    pass