#!/usr/bin/env python

import base64
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'director'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
os.environ.setdefault('DJANGO_CONFIGURATION', 'Prod')
os.environ.setdefault('DJANGO_BETA_TOKEN', 'abc123')
os.environ.setdefault('DJANGO_JWT_SECRET', 'abc123')
os.environ.setdefault('DJANGO_SECRET_KEY', 'abc123')
os.environ.setdefault('DJANGO_SENDGRID_API_KEY', 'abc123')

import django
from django.conf import settings
import configurations

configurations.setup()
django.setup()

from django.utils import timezone

from projects.binder_client import BinderClient, BinderProvider, SPEC_MAP, BuildPhase
from projects.session_models import Session, SessionStatus


def main():
    command = sys.argv[1]
    session_id = sys.argv[2]
    encoded_spec = sys.argv[3]

    if command != 'start-session':
        raise RuntimeError('Unknown command "{}"'.format(command))

    session = Session.objects.get(pk=session_id)

    if session.status not in (SessionStatus.NOT_STARTED, SessionStatus.UNKNOWN):
        raise RuntimeError('Attempting to start a session that is already running or stopped')

    spec_args = json.loads(base64.b64decode(encoded_spec).decode('utf8'))

    spec_type = spec_args.pop('type')

    provider = BinderProvider(spec_type)

    spec_class = SPEC_MAP[provider]

    spec = spec_class(**spec_args)

    bc = BinderClient(settings.BINDER_URL)
    for event in bc.launch(spec):
        if session.log is None:
            session.log = ''

        session.log += '{}: {} {}\n'.format(timezone.now(), event.phase, event.message)
        session.last_check = timezone.now()
        session.save()

        if event.phase == BuildPhase.READY:
            session.started = timezone.now()
            session.url = event.url
            session.save()
            break


if __name__ == '__main__':
    main()
