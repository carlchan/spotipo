# -*- coding: utf-8 -*-
"""Factories to help in tests."""
from factory import Sequence,LazyAttribute
from flask_security.utils import encrypt_password
from factory import Factory
import arrow

from unifispot.core.db import db
from unifispot.core.models import User,Role,Admin,Client,Wifisite


class BaseFactory(Factory):
    """Base factory."""

    class Meta:
        """Factory configuration."""
        abstract = True


class RoleFactory(BaseFactory):
    name = 'admin'
    description = 'Admin'
    class Meta:
        """Factory configuration."""

        model = Role   

class UserFactory(BaseFactory):
    """User factory."""

    email = Sequence(lambda n: 'user{0}@example.com'.format(n))
    displayname = Sequence(lambda n: 'user{0}'.format(n))
    password = LazyAttribute(lambda a: encrypt_password('password'))
    last_login_at = arrow.utcnow().naive
    current_login_at = arrow.utcnow().naive
    confirmed_at = arrow.utcnow().naive
    last_login_ip = '127.0.0.1'
    current_login_ip = '127.0.0.1'
    login_count = 1
    active = True

    class Meta:
        """Factory configuration."""

        model = User        

class AdminFactory(UserFactory):
    """Admin factory."""
    email = Sequence(lambda n: 'admin{0}@example.com'.format(n))

    class Meta:
        """Factory configuration."""

        model = Admin      

class ClientFactory(UserFactory):
    """Admin factory."""
    email = Sequence(lambda n: 'client{0}@example.com'.format(n))

    class Meta:
        """Factory configuration."""

        model = Client  


class WifisiteFactory(BaseFactory):
    name = 'admin'
    default_landing     = 1
    backend             = db.Column(db.String(50))
    template            = 'default'    
    reports_type        = 0
    reports_list        = ''
    redirect_url        = 'http://www.unifispot.com'
    timezone            = 'UTC'


    class Meta:
        """Factory configuration."""
        model = Wifisite           