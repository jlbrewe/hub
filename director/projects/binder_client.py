import base64
import enum
import json
import typing
from subprocess import Popen
from urllib.parse import quote, urljoin

import requests

from projects.client_base import SessionInformation, SessionLocation, SessionAttachContext
from projects.project_models import Project
from projects.session_models import Session, SessionStatus

DATA_SEMAPHORE = b'data: '


class BinderProvider(enum.Enum):
    GIT_HUB = 'gh'
    GIT = 'git'
    GIT_LAB = 'gl'
    GIST = 'gist'


class BinderSpec:
    provider_type: BinderProvider

    def __str__(self) -> str:
        raise NotImplementedError('Subclasses must implement __str__')

    def to_dict(self) -> dict:
        raise NotImplementedError('Subclasses must implement to_dict')


class GitHubSpec(BinderSpec):
    provider_type = BinderProvider.GIT_HUB
    user: str
    repo: str
    ref: str

    def __init__(self, user: str, repo: str, ref: str) -> None:
        self.user = user
        self.repo = repo
        self.ref = ref

    def __str__(self) -> str:
        return '{}/{}/{}'.format(self.user, self.repo, self.ref)

    def to_dict(self) -> dict:
        return {
            'type': self.provider_type.value,
            'user': self.user,
            'repo': self.repo,
            'ref': self.ref
        }


class GitSpec(BinderSpec):
    provider_type = BinderProvider.GIT
    url: str
    commit_sha: str

    def __init__(self, url: str, commit_sha: str) -> None:
        self.url = url
        self.commit_sha = commit_sha

    def __str__(self) -> str:
        return '{}/{}'.format(quote(self.url, safe=''), self.commit_sha)

    def to_dict(self) -> dict:
        return {
            'type': self.provider_type.value,
            'url': self.url,
            'commit_sha': self.commit_sha
        }


class GitLabSpec(BinderSpec):
    provider_type = BinderProvider.GIT_LAB
    namespace: str
    ref: str

    def __init__(self, namespace: str, ref: str) -> None:
        self.namespace = namespace
        self.ref = ref

    def __str__(self) -> str:
        return '{}/{}'.format(quote(self.namespace, safe=''), self.ref)

    def to_dict(self) -> dict:
        return {
            'type': self.provider_type.value,
            'namespace': self.namespace,
            'ref': self.ref
        }


class GistSpec(BinderSpec):
    provider_type = BinderProvider.GIST
    username: str
    ref: str

    def __init__(self, username: str, ref: str) -> None:
        self.username = username
        self.ref = ref

    def __str__(self) -> str:
        return '{}/{}'.format(self.username, self.ref)

    def to_dict(self) -> dict:
        return {
            'type': self.provider_type.value,
            'username': self.username,
            'ref': self.ref
        }


SPEC_MAP = {
    BinderProvider.GIT_HUB: GitHubSpec,
    BinderProvider.GIT: GitSpec,
    BinderProvider.GIT_LAB: GitLabSpec,
    BinderProvider.GIST: GistSpec
}


class BuildPhase(enum.Enum):
    FAILED = 'failed'
    BUILT = 'built'
    WAITING = 'waiting'
    BUILDING = 'building'
    FETCHING = 'fetching'
    PUSHING = 'pushing'
    LAUNCHING = 'launching'
    READY = 'ready'


class BinderEvent(typing.NamedTuple):
    phase: BuildPhase
    message: str
    url: typing.Optional[str]
    token: typing.Optional[str]


class BinderClient:
    base_url: str

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def launch(self, spec: BinderSpec) -> typing.Iterable[BinderEvent]:
        path = 'build/{}/{}'.format(spec.provider_type.value, spec)

        resp = requests.get(urljoin(self.base_url, path), stream=True)

        for line in resp.iter_lines():
            if line.startswith(DATA_SEMAPHORE):
                yield self.parse_event(line[len(DATA_SEMAPHORE):])

    @staticmethod
    def parse_event(event: bytes) -> BinderEvent:
        event_dict = json.loads(event)
        return BinderEvent(
            BuildPhase(event_dict['phase']), event_dict['message'], event_dict.get('url'), event_dict.get('token')
        )


class BinderCliClient(object):
    binder_cli_path: str
    class_id: str = 'BINDER'  # NOQA flake8 is dumb and thinks I am defining a class here so gives E701

    def __init__(self, binder_cli_path: str) -> None:
        self.binder_cli_path = binder_cli_path

    def start_session(self, environ: str, session_parameters: dict, project: Project,
                      spec: BinderSpec) -> SessionAttachContext:
        session = Session.objects.create(project=project, client_class_id=self.class_id)
        session.url = 'binder://{}'.format(session.pk)
        session.save()

        params = [self.binder_cli_path, 'start-session', str(session.pk),
                  base64.b64encode(json.dumps(spec.to_dict()).encode('utf8'))]

        # mypy thinks this is the incorrect type to pass here but it's not
        Popen(params)  # type: ignore

        return SessionAttachContext('', '', session)

    def generate_location(self, session: Session,
                          authorization_extra_parameters: typing.Optional[dict] = None) -> SessionLocation:
        return SessionLocation('', '', '')

    def get_session_info(self, session: Session) -> SessionInformation:
        return SessionInformation(SessionStatus.UNKNOWN)
