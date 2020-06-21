import mimetypes
import os
import re
from typing import Optional, Type, Union

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from polymorphic.models import PolymorphicModel

from jobs.models import Job
from manager.media import private_storage
from projects.models.projects import Project
from users.models import User
from users.socialaccount.tokens import get_user_github_token, get_user_google_token


class SourceAddress(dict):
    """
    A specification of the location of a source.

    Used to store the result of parsing a source address string
    (e.g. a URL), create source instances, specify job parameters,
    filter for existing source instances etc.
    """

    def __init__(self, type_name: str, **kwargs):
        super().__init__(**kwargs)
        self.type_name = type_name
        try:
            self.type = globals()["{}Source".format(type_name)]
        except KeyError:
            raise KeyError('Unknown source type "{}"'.format(type_name))

    def __getattr__(self, attr):
        return self[attr]


def NON_POLYMORPHIC_CASCADE(collector, field, sub_objs, using):
    """
    Cascade delete polymorphic models.

    Without this, a `django.db.utils.IntegrityError: FOREIGN KEY constraint failed` error
    occurs when deleting a project with more than one type of source.
    See https://github.com/django-polymorphic/django-polymorphic/issues/229#issuecomment-398434412
    """
    return models.CASCADE(collector, field, sub_objs.non_polymorphic(), using)


class Source(PolymorphicModel):
    """
    A project source.
    """

    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=NON_POLYMORPHIC_CASCADE,
        related_name="sources",
    )

    path = models.TextField(
        null=False,
        blank=False,
        help_text="The path that the file or directory from the source is mapped to in the project",
    )

    creator = models.ForeignKey(
        User,
        null=True,  # Should only be null if the creator is deleted
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sources_created",
        help_text="The user who created the source.",
    )

    created = models.DateTimeField(
        auto_now_add=True, help_text="The time the source was created."
    )

    updated = models.DateTimeField(
        auto_now=True, help_text="The time the source was last changed"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "path"], name="%(class)s_unique_project_path"
            )
        ]

    @property
    def type(self) -> Type["Source"]:
        """Get the type of a source instance e.g. `GoogleDocsSource`."""
        return ContentType.objects.get_for_id(self.polymorphic_ctype_id).model

    @property
    def type_name(self) -> str:
        """
        Get the name of the type of a source instance.

        The `type_name` is intended for use in user interfaces.
        This base implementation simply drops `Source` from the end
        of the name. Can be overridden in derived classes if
        necessary.
        """
        return self.__class__.__name__[:-6]

    def __str__(self) -> str:
        """
        Get a human readable string representation of the source instance.

        These are intended to be URL-like human-readable and -writable shorthand
        representations of sources (e.g. `github://org/repo/sub/path`; `gdoc://378yfh2yg362...`).
        They are used in admin lists and in API endpoints to allowing quick
        specification of a source (e.g. for filtering).
        Should be parsable by the `parse_address` method of each subclass.

        In addition, subclasses should implement a `url` property
        that returns a valid URL that is a "backlink" to the source.
        """
        return "{}://{}".format(self.type_name.lower(), self.id)

    @property
    def provider_name(self) -> str:
        """
        Get the name of the provider of a source instance.

        Intended mainly for user interfaces (e.g. to send a message to a client
        that they need to authenticate with a provider in order to
        use a particular source type). Will usually be the same as the `type_name`,
        but derived classes can override if not.
        """
        return self.type_name

    @staticmethod
    def class_from_type_name(type_name: str) -> Type["Source"]:
        """Find the class matching the type name."""
        for cls in Source.__subclasses__():
            if cls.__name__.lower().startswith(type_name.lower()):
                return cls

        raise ValueError('Unable to find class matching "{}"'.format(type_name))

    @staticmethod
    def coerce_address(address: Union[SourceAddress, str]) -> SourceAddress:
        """
        Coerce a string into a `SourceAddress`.

        If the `address` is already an instance of `SourceAddress` it
        will be returned unchanged. Otherwise, the `parse_address`
        method of each source type (ie. subclass of `Source`) will
        be called. The first class that returns a `SourceAddress` wins.
        """
        if isinstance(address, SourceAddress):
            return address

        for cls in Source.__subclasses__():
            result = cls.parse_address(address)
            if result is not None:
                return result

        raise ValueError('Unable to parse source address "{}"'.format(address))

    @classmethod
    def parse_address(
        cls, address: str, naked: bool = False, strict: bool = False
    ) -> Optional[SourceAddress]:
        """
        Parse a string into a `SourceAddress`.

        This default implementation just matches the default string
        representation of a source, as generated by `Source.__str__`.
        Derived classes should override this method to match their own
        `__str__` method.
        """
        type_name = cls.__name__[:-6]
        if address.startswith(type_name.lower() + "://"):
            return SourceAddress(type_name)

        if strict:
            raise ValidationError("Invalid source identifier: {}".format(address))

        return None

    @staticmethod
    def query_from_address(
        address_or_string: Union[SourceAddress, str], prefix: Optional[str] = None,
    ) -> models.Q:
        """
        Create a query object for a source address.

        Given a source address, constructs a Django `Q` object which
        can be used in ORM queries. Use the `prefix` argument
        when you want to use this function for a related field. For example,

            Source.query_from_address({
                "type": "Github",
                "repo": "org/repo",
                "subpath": "folder"
            }, prefix="sources")

        is equivalent to :

            Q(
                sources__githubsource__repo="org/repo",
                sources__githubsource__subpath="folder"
            )
        """
        address = Source.coerce_address(address_or_string)

        front = (
            "{}__".format(prefix) if prefix else ""
        ) + address.type.__name__.lower()
        kwargs = dict(
            [("{}__{}".format(front, key), value) for key, value in address.items()]
        )
        return models.Q(**kwargs)

    @staticmethod
    def from_address(address_or_string: Union[SourceAddress, str]) -> "Source":
        """
        Create a source instance from a source address.

        Given a source address, creates a new source instance of the
        specified `type` with fields set from the address.
        """
        address = Source.coerce_address(address_or_string)
        return address.type.objects.create(**address)

    def to_address(self) -> SourceAddress:
        """
        Create a source address from a source instance.

        The inverse of `Source.from_address`. Used primarily
        to create a pull job for a source.
        """
        all_fields = [field.name for field in self._meta.fields]
        class_fields = [
            name for name in self.__class__.__dict__.keys() if name in all_fields
        ]
        return SourceAddress(
            self.type_name,
            **dict(
                [
                    (name, value)
                    for name, value in self.__dict__.items()
                    if name in class_fields
                ],
                type=self.type_name,
            ),
        )

    @staticmethod
    def mimetype_from_path(path: str, default: str = "unknown") -> str:
        """
        Get the mimetype of a file from its path.

        Returns custom mimetype for a directory if the path
        does not have an extension.
        Returns the `default` if the mimetype can not be guessed.
        """
        extension = os.path.splitext(path)[1]
        if not extension:
            return "application/x-directory"
        else:
            mimetype, encoding = mimetypes.guess_type(path, False)
            return mimetype or default

    @property
    def mimetype(self) -> str:
        """
        Get the mimetype of the source.

        Derived classes should override this if an attribute of the source
        other than the local `path` should be used to determine the mimetype
        e.g. if it is always a Google Doc.
        """
        return Source.mimetype_from_path(self.path)

    def absolute_path(self) -> str:
        """
        Get the absolute path of the source within the project's working directory.
        """
        return os.path.join(
            settings.STORAGE_DIR, "projects", str(self.project.id), "working", self.path
        )

    def pull(self, user: User) -> Job:
        """
        Pull the source to the filesystem.

        Creates a `Job` having the `pull` method and a dictionary of `source`
        attributes sufficient to pull it. This may include authentication tokens.
        """
        return Job.objects.create(
            creator=user,
            method="pull",
            params=dict(
                source=self.to_address(), project=self.project.id, path=self.path
            ),
        )

    def push(self) -> Job:
        """
        Push from the filesystem to the source.

        Creates a `Job` having the `push` method and a dictionary of `source`
        attributes sufficient to push it. This may include authentication tokens.
        """
        raise NotImplementedError(
            "Push is not implemented for class {}".format(self.__class__.__name__)
        )

    def save(self, *args, **kwargs):
        """Override of save."""
        # Make sure there are no leading or trailing slashes in the path to
        # make them consistent
        self.path = self.path.strip("/")
        super().save(*args, **kwargs)


# Source classes in alphabetical order


class ElifeSource(Source):
    """An article from https://elifesciences.org."""

    article = models.IntegerField(help_text="The article number.")

    version = models.IntegerField(
        null=True,
        blank=True,
        help_text="The article version. If blank, defaults to the latest.",
    )

    @property
    def url(self):
        """Get the URL of the article on the eLife website."""
        return "https://elifesciences.org/articles/{0}".format(self.article)

    @property
    def mimetype(self) -> str:
        """Get the mimetype of an eLife article."""
        return "text/xml+jats"


class GithubSource(Source):
    """A project hosted on Github."""

    repo = models.CharField(
        max_length=512,
        null=False,
        blank=False,
        help_text="The Github repository identifier i.e. org/repo",
    )

    subpath = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        help_text="Path to file or folder within the repository",
    )

    def __str__(self) -> str:
        return (
            "github://"
            + self.repo
            + ("/{}".format(self.subpath) if self.subpath else "")
        )

    @property
    def url(self):
        """Get the URL of a GitHub source."""
        url = "https://github.com/{}".format(self.repo)
        if self.subpath:
            url += "/blob/master/{}".format(self.subpath)
        return url

    @property
    def mimetype(self) -> str:
        """Get the mimetype of a GitHub source."""
        return Source.mimetype_from_path(self.subpath) if self.subpath else "unknown"

    @classmethod
    def parse_address(
        cls, address: str, naked: bool = False, strict: bool = False
    ) -> Optional[SourceAddress]:
        """Parse a string into a GitHub `SourceAddress`."""
        match = re.search(
            r"^github://((?:[a-z0-9\-]+)/(?:[a-z0-9\-_]+))/?(.+)?$", address, re.I
        )
        if match:
            return SourceAddress("Github", repo=match.group(1), subpath=match.group(2))

        match = re.search(
            r"^(?:https?://)?github\.com/((?:[a-z0-9\-]+)/(?:[a-z0-9\-_]+))/?(?:(?:tree|blob)/(?:[^/]+)/(.+))?$",
            address,
            re.I,
        )
        if match:
            return SourceAddress("Github", repo=match.group(1), subpath=match.group(2))

        if strict:
            raise ValidationError(
                "Invalid Github source identifier: {}".format(address)
            )

        return None

    def pull(self, user: User) -> Job:
        """Pull a Github source to the filesystem."""
        source_address = self.to_address()
        source_address["token"] = get_user_github_token(user)

        return Job.objects.create(
            creator=user,
            method="pull",
            params=dict(source=source_address, project=self.project.id, path=self.path),
        )


class GoogleDocsSource(Source):
    """A reference to a Google Docs document."""

    doc_id = models.TextField(
        null=False,
        help_text="The id of the document e.g. 1iNeKTanIcW_92Hmc8qxMkrW2jPrvwjHuANju2hkaYkA",
    )

    @property
    def provider_name(self) -> str:
        """Get the provider name for a Google Doc."""
        return "Google"

    def __str__(self) -> str:
        return "gdoc://{}".format(self.doc_id)

    @property
    def url(self) -> str:
        """Get the URL of a Google Doc."""
        return "https://docs.google.com/document/d/{}/edit".format(self.doc_id)

    @property
    def mimetype(self) -> str:
        """Get the mimetype of an Google Doc."""
        return "application/vnd.google-apps.document"

    @classmethod
    def parse_address(
        cls, address: str, naked: bool = False, strict: bool = False
    ) -> Optional[SourceAddress]:
        """Parse a string into a Google Doc address."""
        doc_id = None

        match = re.search(r"^gdoc://(.+)$", address, re.I)
        if match:
            doc_id = match.group(1)

        match = re.search(
            r"^(?:https://)?docs.google.com/document/d/([^/]+)/?.*", address, re.I
        )
        if match:
            doc_id = match.group(1)

        # No match so far, maybe a naked doc id was supplied
        if naked and not doc_id:
            doc_id = address

        # Check it's a valid id
        if doc_id:
            if not re.match(r"^([a-z\d])([a-z\d_\-]{10,})$", doc_id, re.I):
                doc_id = None

        if doc_id:
            return SourceAddress("GoogleDocs", doc_id=doc_id)

        if strict:
            raise ValidationError("Invalid Google Doc identifier: {}".format(address))

        return None

    def pull(self, user: User) -> Job:
        """Pull a Google Doc into the project folder."""
        source_address = self.to_address()
        source_address["token"] = get_user_google_token(user)

        return Job.objects.create(
            creator=user,
            method="pull",
            params=dict(source=source_address, project=self.project.id, path=self.path),
        )


class GoogleDriveSource(Source):
    """A reference to a Google Drive folder."""

    folder_id = models.TextField(null=False, help_text="Google's ID of the folder.")

    @property
    def provider_name(self) -> str:
        """Get the provider name for a Google Drive source."""
        return "Google"

    def pull(self, user: User) -> Job:
        """Pull a Google Drive folder into the project folder."""
        source_address = self.to_address()
        source_address["token"] = get_user_google_token(user)

        return Job.objects.create(
            creator=user,
            method="pull",
            params=dict(source=source_address, project=self.project.id, path=self.path),
        )


class PlosSource(Source):
    """An article from https://journals.plos.org."""

    article = models.TextField(help_text="The article DOI.")

    @property
    def mimetype(self) -> str:
        """Get the mimetype of an PLOS article."""
        return "text/xml+jats"


def upload_source_path(instance, filename):
    """
    Get the path to upload the file to.

    To avoid a lot of files in a single directory,
    nests within project.
    """
    return "projects/{project}/sources/upload-{id}-{filename}".format(
        project=instance.project.id, id=instance.id, filename=filename
    )


class UploadSource(Source):
    """
    A file that has been uploaded to the Hub.

    This allows us to keep track of files that have been explicitly
    uploaded to the project folder, rather than being derived from
    pulling other sources, or being derived from jobs.
    """

    file = models.FileField(
        storage=private_storage(),
        upload_to=upload_source_path,
        help_text="The uploaded file.",
    )

    def __str__(self) -> str:
        return "upload://{}".format(self.path)


class UrlSource(Source):
    """A source that is downloaded from a URL on demand."""

    url = models.URLField(help_text="The URL of the remote file.")

    def __str__(self) -> str:
        return self.url

    @property
    def mimetype_(self) -> str:
        """Get the mimetype of a URL source."""
        return Source.mimetype_from_path(self.url)

    @classmethod
    def parse_address(
        cls, address: str, naked: bool = False, strict: bool = False
    ) -> Optional[SourceAddress]:
        """Parse a string into a URL `SourceAddress`."""
        url: Optional[str] = address
        try:
            URLValidator()(url)
        except ValidationError:
            url = None

        if url:
            return SourceAddress("Url", url=url)

        if strict:
            raise ValidationError("Invalid URL source: {}".format(address))

        return None