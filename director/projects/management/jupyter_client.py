import typing

from projects.client_base import SessionInformation, SessionLocation, SessionAttachContext, RestClientBase, HttpMethod
from projects.session_models import Session


class JupyterClient(RestClientBase):
    # WIP
    auth_token: str

    def __init__(self, base_url: str, server_proxy_path: str, auth_token: str) -> None:
        super().__init__(base_url, server_proxy_path)
        self.auth_token = auth_token

    def user_server_is_running(self, username: str, pod_name: str) -> bool:
        """Check a user has a server with the given pod_name (environment identifier) running."""
        resp = self.make_request(HttpMethod.GET, self.get_full_url('hub/api/users/{}'.format(username)))
        for server_id, server_model in resp['servers'].items():
            if server_model['state']['pod_name'] == pod_name and server_model['ready']:
                return True

        return False

    def start_user_server(self, username: str, pod_name: str) -> None:
        if self.user_server_is_running(username, pod_name):
            return
        self.make_request(HttpMethod.POST, self.get_full_url('hub/api/users/{}/server'.format(username)))

    def get_user_kernels(self, username: str) -> typing.List[dict]:
        resp = self.make_request(HttpMethod.POST, self.get_full_url('user/{}/api/kernels'.format(username)))
        print(resp)

    def start_session_for_kernel(self, username: str, kernel_name: str) -> None:
        resp = self.make_request(HttpMethod.POST, self.get_full_url('user/{}/api/sessions'.format(username)),
                                 body_data={'path': 'randompath',
                                            'type': 'console',
                                            'kernel': {'name': kernel_name,
                                                       'id': None}})
        print(resp)

    def start_session(self, environ: str, session_parameters: dict) -> SessionAttachContext:
        username = session_parameters['username']
        pod_name = 'jupyter-{}'.format(username)

        self.start_user_server(username, pod_name)
        self.get_user_kernels(username)
        self.start_session_for_kernel(username, environ)

    def generate_location(self, session: Session,
                          authorization_extra_parameters: typing.Optional[dict] = None) -> SessionLocation:
        pass

    def get_session_info(self, session: Session) -> SessionInformation:
        pass

    def get_authorization_header(self, extra_payload: typing.Optional[dict] = None) -> typing.Dict[str, str]:
        return {
            "Authorization": "token {}".format(self.auth_token)
        }
