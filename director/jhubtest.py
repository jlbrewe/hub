import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'director'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
os.environ.setdefault('DJANGO_CONFIGURATION', 'Prod')
os.environ.setdefault('DJANGO_BETA_TOKEN', 'abc123')
os.environ.setdefault('DJANGO_JWT_SECRET', 'abc123')
os.environ.setdefault('DJANGO_SECRET_KEY', 'abc123')
os.environ.setdefault('DJANGO_SENDGRID_API_KEY', 'abc123')

import django  # noqa: E402
import configurations  # noqa: E402

configurations.setup()
django.setup()

from projects.management.jupyter_client import JupyterClient  # noqa: E402

# these might look like secret things but they are only for my local deploy so it doesn't matter if they go to GitHub

api_url = 'http://172.16.6.130:31212/'

token = '0cc05feaefeeb29179e924ffc6d3886ffacf0d1a28ab225f5c210436ffc5cfd5'

client = JupyterClient(api_url, '', token)

client.start_session('python3', {'username': 'ben'})
