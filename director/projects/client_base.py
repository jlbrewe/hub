import enum
import time
import typing
from urllib.parse import urljoin

import jwt
import requests

from projects.session_models import SessionStatus, Session

JWT_ALGORITHM = "HS256"


class HttpMethod(enum.Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    OPTIONS = 'OPTIONS'


class SessionInformation(typing.NamedTuple):
    status: SessionStatus  # This is probably only going to be RUNNING or STOPPED


class SessionAttachContext(typing.NamedTuple):
    url: str
    execution_id: str = ''

    def to_dict(self) -> dict:
        return {'execution_id': self.execution_id, 'url': self.url}


class RestClientBase(object):
    host_url: str
    jwt_secret: str

    def __init__(self, host_url: str, jwt_secret: str) -> None:
        self.host_url = host_url + "/" if not host_url.endswith("/") else host_url  # ensure trailing /
        self.jwt_secret = jwt_secret

    def get_authorization_header(self, extra_payload: typing.Optional[dict] = None) -> typing.Dict[str, str]:
        return {
            "Authorization": "Bearer {}".format(self.generate_jwt_token(extra_payload))
        }

    def make_request(self, method: HttpMethod, url: str, extra_jwt_payload: typing.Optional[dict] = None,
                     body_data: typing.Optional[dict] = None) -> dict:
        # TODO: add `SessionParameters` to the POST body (currently they won't do anything anyway)
        response = requests.request(method.value, url, headers=self.get_authorization_header(extra_jwt_payload),
                                    json=body_data)
        response.raise_for_status()

        try:
            return response.json()
        except Exception:
            raise Exception('Error parsing body: ' + response.text)

    def get_full_url(self, path: str) -> str:
        return urljoin(self.host_url, path)

    def generate_jwt_token(self, extra_payload: typing.Optional[dict] = None) -> str:
        """Create a JWT token for the host."""
        jwt_payload = {"iat": time.time()}

        if extra_payload:
            jwt_payload.update(extra_payload)

        return jwt.encode(jwt_payload, self.jwt_secret, algorithm=JWT_ALGORITHM).decode("utf-8")

    def start_session(self, environ: str, session_parameters: dict) -> SessionAttachContext:
        raise NotImplementedError('Subclasses must implement start_session')

    def generate_authorization_token(self, execution_id: typing.Optional[str]) -> str:
        """Intended to be overridden but a safe default."""
        return ''

    def get_session_info(self, session: Session) -> SessionInformation:
        """Get information about the session. At this stage we are only interested in its status."""
        raise NotImplementedError('Subclasses must implement get_session_info')
