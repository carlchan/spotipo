from unifispot.core.models import Account,Admin,Client,Wifisite
from unifispot.core.db import db as _db
from tests.factories import UserFactory,AdminFactory,ClientFactory,WifisiteFactory
from flask_security.utils import encrypt_password


def init_data(session):

    account1 = Account(name='Account1')
    session.add(account1)

    account2 = Account(name='Account2')
    session.add(account2)

    session.commit()

    admin1 = AdminFactory(email='admin1@example.com')
    admin1.account_id = account1.id
    session.add(admin1)

    admin2 = AdminFactory(email='admin2@example.com')
    admin2.account_id = account2.id
    session.add(admin2)

    client1 = ClientFactory(email='client1@example.com')
    client1.account_id = account1.id
    session.add(client1)

    client2 = ClientFactory(email='client2@example.com')
    client2.account_id = account2.id
    session.add(client2)
    session.commit()

    client3 = ClientFactory(email='client3@example.com')
    client3.account_id = account1.id
    session.add(client3)
    session.commit()    

    site1 = Wifisite(backend_type='unifi',sitekey='default')
    site1.client_id = client1.id
    site1.account_id = account1.id
    session.add(site1)


    site2 = Wifisite()
    site2.client_id = client2.id
    site2.account_id = account2.id
    session.add(site2)

    site3 = Wifisite(backend_type='unifi',sitekey='default')
    site3.client_id = client3.id
    site3.account_id = account1.id
    session.add(site3)


    session.commit()

    
