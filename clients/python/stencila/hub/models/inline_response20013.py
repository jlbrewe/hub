# coding: utf-8

"""
    Stencila Hub API

    ## Authentication  Many endpoints in the Stencila Hub API require an authentication token. These tokens carry many privileges, so be sure to keep them secure. Do not place your tokens in publicly accessible areas such as client-side code. The API is only served over HTTPS to avoid exposing tokens and other data on the network.  To obtain a token, [`POST /api/tokens`](#operations-tokens-tokens_create) with either a `username` and `password` pair, or an [OpenID Connect](https://openid.net/connect/) token. Then use the token in the `Authorization` header of subsequent requests with the prefix `Token` e.g.      curl -H \"Authorization: Token 48866b1e38a2e9db0baada2140b2327937f4a3636dd5f2dfd8c212341c88d34\" https://hub.stenci.la/api/projects/  Alternatively, you can use `Basic` authentication with the token used as the username and no password. This can be more convenient when using command line tools such as [cURL](https://curl.haxx.se/) e.g.      curl -u 48866b1e38a2e9db0baada2140b2327937f4a3636dd5f2dfd8c212341c88d34: https://hub.stenci.la/api/projects/  Or, the less ubiquitous, but more accessible [httpie](https://httpie.org/):      http --auth 48866b1e38a2e9db0baada2140b2327937f4a3636dd5f2dfd8c212341c88d34: https://hub.stenci.la/api/projects/  In both examples above, the trailing colon is not required but avoids being asked for a password.  ## Versioning  The Stencila Hub is released using semantic versioning. The current version is available from the [`GET /api/status`](/api/status) endpoint. Please see the [Github release page](https://github.com/stencila/hub/releases) and the [changelog](https://github.com/stencila/hub/blob/master/CHANGELOG.md) for details on each release. We currently do not provide versioning of the API but plan to do so soon (probably by using a `Accept: application/vnd.stencila.hub+json;version=1.0` request header). If you are using, or interested in using, the API please contact us and we may be able to expedite this.   # noqa: E501

    The version of the OpenAPI document: v1
    Generated by: https://openapi-generator.tech
"""


import pprint
import re  # noqa: F401

import six

from stencila.hub.configuration import Configuration


class InlineResponse20013(object):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    openapi_types = {
        'count': 'int',
        'next': 'str',
        'previous': 'str',
        'results': 'list[Source]'
    }

    attribute_map = {
        'count': 'count',
        'next': 'next',
        'previous': 'previous',
        'results': 'results'
    }

    def __init__(self, count=None, next=None, previous=None, results=None, local_vars_configuration=None):  # noqa: E501
        """InlineResponse20013 - a model defined in OpenAPI"""  # noqa: E501
        if local_vars_configuration is None:
            local_vars_configuration = Configuration()
        self.local_vars_configuration = local_vars_configuration

        self._count = None
        self._next = None
        self._previous = None
        self._results = None
        self.discriminator = None

        self.count = count
        self.next = next
        self.previous = previous
        self.results = results

    @property
    def count(self):
        """Gets the count of this InlineResponse20013.  # noqa: E501


        :return: The count of this InlineResponse20013.  # noqa: E501
        :rtype: int
        """
        return self._count

    @count.setter
    def count(self, count):
        """Sets the count of this InlineResponse20013.


        :param count: The count of this InlineResponse20013.  # noqa: E501
        :type count: int
        """
        if self.local_vars_configuration.client_side_validation and count is None:  # noqa: E501
            raise ValueError("Invalid value for `count`, must not be `None`")  # noqa: E501

        self._count = count

    @property
    def next(self):
        """Gets the next of this InlineResponse20013.  # noqa: E501


        :return: The next of this InlineResponse20013.  # noqa: E501
        :rtype: str
        """
        return self._next

    @next.setter
    def next(self, next):
        """Sets the next of this InlineResponse20013.


        :param next: The next of this InlineResponse20013.  # noqa: E501
        :type next: str
        """

        self._next = next

    @property
    def previous(self):
        """Gets the previous of this InlineResponse20013.  # noqa: E501


        :return: The previous of this InlineResponse20013.  # noqa: E501
        :rtype: str
        """
        return self._previous

    @previous.setter
    def previous(self, previous):
        """Sets the previous of this InlineResponse20013.


        :param previous: The previous of this InlineResponse20013.  # noqa: E501
        :type previous: str
        """

        self._previous = previous

    @property
    def results(self):
        """Gets the results of this InlineResponse20013.  # noqa: E501


        :return: The results of this InlineResponse20013.  # noqa: E501
        :rtype: list[Source]
        """
        return self._results

    @results.setter
    def results(self, results):
        """Sets the results of this InlineResponse20013.


        :param results: The results of this InlineResponse20013.  # noqa: E501
        :type results: list[Source]
        """
        if self.local_vars_configuration.client_side_validation and results is None:  # noqa: E501
            raise ValueError("Invalid value for `results`, must not be `None`")  # noqa: E501

        self._results = results

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.openapi_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, InlineResponse20013):
            return False

        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, InlineResponse20013):
            return True

        return self.to_dict() != other.to_dict()
