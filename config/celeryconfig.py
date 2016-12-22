import os
BROKER_URL = 'sqla+sqlite:///'+os.path.join(os.path.abspath(os.path.dirname(__file__)),'..','instance','celerydb.db')
