# coding: utf-8

"""
    Stencila Hub API

    ## Authentication  Many endpoints in the Stencila Hub API require an authentication token. These tokens carry many privileges, so be sure to keep them secure. Do not place your tokens in publicly accessible areas such as client-side code. The API is only served over HTTPS to avoid exposing tokens and other data on the network.  To obtain a token, [`POST /api/tokens`](#operations-tokens-tokens_create) with either a `username` and `password` pair, or an [OpenID Connect](https://openid.net/connect/) token. Then use the token in the `Authorization` header of subsequent requests with the prefix `Token` e.g.      curl -H \"Authorization: Token 48866b1e38a2e9db0baada2140b2327937f4a3636dd5f2dfd8c212341c88d34\" https://hub.stenci.la/api/projects/  Alternatively, you can use `Basic` authentication with the token used as the username and no password. This can be more convenient when using command line tools such as [cURL](https://curl.haxx.se/) e.g.      curl -u 48866b1e38a2e9db0baada2140b2327937f4a3636dd5f2dfd8c212341c88d34: https://hub.stenci.la/api/projects/  Or, the less ubiquitous, but more accessible [httpie](https://httpie.org/):      http --auth 48866b1e38a2e9db0baada2140b2327937f4a3636dd5f2dfd8c212341c88d34: https://hub.stenci.la/api/projects/  In both examples above, the trailing colon is not required but avoids being asked for a password.  ## Versioning  The Stencila Hub is released using semantic versioning. The current version is available from the [`GET /api/status`](/api/status) endpoint. Please see the [Github release page](https://github.com/stencila/hub/releases) and the [changelog](https://github.com/stencila/hub/blob/master/CHANGELOG.md) for details on each release. We currently do not provide versioning of the API but plan to do so soon (probably by using a `Accept: application/vnd.stencila.hub+json;version=1.0` request header). If you are using, or interested in using, the API please contact us and we may be able to expedite this.   # noqa: E501

    The version of the OpenAPI document: v1
    Generated by: https://openapi-generator.tech
"""


from __future__ import absolute_import

import re  # noqa: F401

# python 2 and python 3 compatibility library
import six

from stencila.hub.api_client import ApiClient
from stencila.hub.exceptions import (  # noqa: F401
    ApiTypeError,
    ApiValueError
)


class StatusApi(object):
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    def __init__(self, api_client=None):
        if api_client is None:
            api_client = ApiClient()
        self.api_client = api_client

    def status_read(self, **kwargs):  # noqa: E501
        """status_read  # noqa: E501

        Get the system status.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.status_read(async_req=True)
        >>> result = thread.get()

        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: StatusResponse
        """
        kwargs['_return_http_data_only'] = True
        return self.status_read_with_http_info(**kwargs)  # noqa: E501

    def status_read_with_http_info(self, **kwargs):  # noqa: E501
        """status_read  # noqa: E501

        Get the system status.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.status_read_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(StatusResponse, status_code(int), headers(HTTPHeaderDict))
        """

        local_var_params = locals()

        all_params = [
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout',
                '_request_auth'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method status_read" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['Token']  # noqa: E501

        return self.api_client.call_api(
            '/status/', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='StatusResponse',  # noqa: E501
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats,
            _request_auth=local_var_params.get('_request_auth'))
