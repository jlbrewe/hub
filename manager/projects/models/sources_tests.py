import pytest
from django.core.exceptions import ValidationError
from django.db.models import Q

from accounts.models import Account, AccountTier
from manager.testing import DatabaseTestCase
from projects.models.projects import Project
from projects.models.sources import (
    ElifeSource,
    GithubSource,
    GoogleDocsSource,
    GoogleDriveSource,
    GoogleSheetsSource,
    Source,
    SourceAddress,
    UploadSource,
    UrlSource,
)


def test_source_address():
    with pytest.raises(KeyError, match='Unknown source type "foo"'):
        SourceAddress("foo")


def test_coerce_address():
    # A specific address (ie. starting with type://)
    sa = Source.coerce_address("github://org/repo/a/file.md")
    assert sa.type == GithubSource
    assert sa["repo"] == "org/repo"
    assert sa["subpath"] == "a/file.md"

    sa = Source.coerce_address("gsheet://1BW6MubIyDirCGW9Wq-tSqCma8pioxBI6VpeLyXn5mZA")
    assert sa.type == GoogleSheetsSource
    assert sa["doc_id"] == "1BW6MubIyDirCGW9Wq-tSqCma8pioxBI6VpeLyXn5mZA"

    # A HTTP URL that is matched by a specific source
    sa = Source.coerce_address("https://github.com/org/repo")
    assert sa.type == GithubSource

    # A generic URL that caught as a URL source
    sa = Source.coerce_address("https://example.org/file.R")
    assert sa.type == UrlSource

    # An address that is not matched by any source type
    with pytest.raises(ValueError, match='Unable to parse source address "foo"'):
        sa = Source.coerce_address("foo")


def test_default_make_address():
    assert ElifeSource(article=43143).make_address() == "elife://43143"


def test_default_parse_address():
    sa = ElifeSource.parse_address("elife://")
    assert sa.type == ElifeSource

    sa = ElifeSource.parse_address("foo")
    assert sa is None

    with pytest.raises(ValidationError):
        ElifeSource.parse_address("foo", strict=True)


def test_query_from_address():
    q = Source.query_from_address(SourceAddress("Github", repo="org/repo"))
    assert isinstance(q, Q)
    assert q.children == [("githubsource__repo", "org/repo")]

    q = Source.query_from_address(
        SourceAddress("Github", repo="org/repo", subpath="a/sub/folder")
    )
    assert q.children == [
        ("githubsource__repo", "org/repo"),
        ("githubsource__subpath", "a/sub/folder"),
    ]

    q = Source.query_from_address(
        SourceAddress("Github", repo="org/repo"), prefix="sources"
    )
    assert q.children == [("sources__githubsource__repo", "org/repo")]

    q = Source.query_from_address(
        SourceAddress("Github", repo="org/repo", subpath="a/sub/folder"),
        prefix="sources",
    )
    assert q.children == [
        ("sources__githubsource__repo", "org/repo"),
        ("sources__githubsource__subpath", "a/sub/folder"),
    ]

    q1 = Source.query_from_address("upload://foo.txt")
    q2 = Source.query_from_address(SourceAddress("Upload", name="foo.txt"))
    assert q1.children == [("uploadsource__name", "foo.txt")]
    assert q2 == q1


@pytest.mark.django_db
def test_from_address():
    s = Source.from_address(
        SourceAddress("Github", repo="org/repo", subpath="a/folder")
    )
    assert isinstance(s, GithubSource)
    assert s.repo == "org/repo"
    assert s.subpath == "a/folder"

    s = Source.from_address("github://org/repo")
    assert isinstance(s, GithubSource)
    assert s.repo == "org/repo"
    assert s.subpath is None


def test_to_address():
    s = GithubSource(repo="org/repo", subpath="a/folder")
    a = s.to_address()
    assert a.type_name == "Github"
    assert list(a.keys()) == ["repo", "subpath"]
    assert a.repo == "org/repo"
    assert a.subpath == "a/folder"


def test_githubsource_make_address():
    assert GithubSource(repo="user/repo").make_address() == "github://user/repo"
    assert (
        GithubSource(repo="user/repo", subpath="a/file.txt").make_address()
        == "github://user/repo/a/file.txt"
    )


def test_githubsource_url():
    assert GithubSource(repo="user/repo").get_url() == "https://github.com/user/repo"
    assert (
        GithubSource(repo="user/repo", subpath="a/file.txt").get_url()
        == "https://github.com/user/repo/blob/master/a/file.txt/"
    )


def test_githubsource_parse_address():
    for url in [
        "github://django/django",
        "http://github.com/django/django",
        "https://github.com/django/django/",
    ]:
        sa = GithubSource.parse_address(url)
        assert sa.type == GithubSource
        assert sa["repo"] == "django/django"
        assert sa["subpath"] is None

    for url in [
        "github://django/django/django/db/models",
        "http://github.com/django/django/tree/master/django/db/models",
        "https://github.com/django/django/tree/master/django/db/models",
    ]:
        sa = GithubSource.parse_address(url)
        assert sa.type == GithubSource
        assert sa["repo"] == "django/django"
        assert sa["subpath"] == "django/db/models"

    for url in [
        "github://django/django/django/db/models/query_utils.py",
        "https://github.com/django/django/blob/master/django/db/models/query_utils.py",
    ]:
        sa = GithubSource.parse_address(url)
        assert sa.type == GithubSource
        assert sa["repo"] == "django/django"
        assert sa["subpath"] == "django/db/models/query_utils.py"


def test_googledocssource_make_address():
    assert GoogleDocsSource(doc_id="an-id").make_address() == "gdoc://an-id"


def test_googledocssource_to_address():
    a = GoogleDocsSource(doc_id="an-id").to_address()
    assert a.type_name == "GoogleDocs"
    assert list(a.keys()) == ["doc_id"]
    assert a.doc_id == "an-id"


def test_googledocssource_url():
    assert (
        GoogleDocsSource(doc_id="an-id").get_url()
        == "https://docs.google.com/document/d/an-id/edit"
    )


def test_googledocssource_parse_address():
    for url in [
        "gdoc://1BW6MubIyDirCGW9Wq-tSqCma8pioxBI6VpeLyXn5mZA",
        "docs.google.com/document/d/1BW6MubIyDirCGW9Wq-tSqCma8pioxBI6VpeLyXn5mZA",
        "https://docs.google.com/document/d/1BW6MubIyDirCGW9Wq-tSqCma8pioxBI6VpeLyXn5mZA/",
        "https://docs.google.com/document/d/1BW6MubIyDirCGW9Wq-tSqCma8pioxBI6VpeLyXn5mZA/edit",
    ]:
        sa = GoogleDocsSource.parse_address(url)
        assert sa.type == GoogleDocsSource
        assert sa.doc_id == "1BW6MubIyDirCGW9Wq-tSqCma8pioxBI6VpeLyXn5mZA"

    # Use of naked ids
    assert (
        GoogleDocsSource.parse_address("1BW6MubIyDirCGW9Wq-tSqCma8pioxBI6VpeLyXn5mZA")
        is None
    )
    assert (
        GoogleDocsSource.parse_address(
            "1BW6MubIyDirCGW9Wq-tSqCma8pioxBI6VpeLyXn5mZA", naked=True
        ).doc_id
        == "1BW6MubIyDirCGW9Wq-tSqCma8pioxBI6VpeLyXn5mZA"
    )

    # Use of strict
    assert GoogleDocsSource.parse_address("foo") is None
    with pytest.raises(ValidationError, match="Invalid Google Doc identifier"):
        GoogleDocsSource.parse_address("foo", strict=True)


def test_googlesheetssource_make_address():
    assert GoogleSheetsSource(doc_id="an-id").make_address() == "gsheet://an-id"


def test_googlesheetssource_to_address():
    a = GoogleSheetsSource(doc_id="an-id").to_address()
    assert a.type_name == "GoogleSheets"
    assert list(a.keys()) == ["doc_id"]
    assert a.doc_id == "an-id"


def test_googlesheetssource_url():
    assert (
        GoogleSheetsSource(doc_id="an-id").get_url()
        == "https://docs.google.com/spreadsheets/d/an-id/edit"
    )


def test_googlesheetssource_parse_address():
    for url in [
        "gsheet://1BW6MubIyDirCGW9Wq-tSqCma8pioxBI6VpeLyXn5mZA",
        "docs.google.com/spreadsheets/d/1BW6MubIyDirCGW9Wq-tSqCma8pioxBI6VpeLyXn5mZA",
        "https://docs.google.com/spreadsheets/d/1BW6MubIyDirCGW9Wq-tSqCma8pioxBI6VpeLyXn5mZA/",
        "https://docs.google.com/spreadsheets/d/1BW6MubIyDirCGW9Wq-tSqCma8pioxBI6VpeLyXn5mZA/edit",
    ]:
        sa = GoogleSheetsSource.parse_address(url)
        assert sa.type == GoogleSheetsSource
        assert sa.doc_id == "1BW6MubIyDirCGW9Wq-tSqCma8pioxBI6VpeLyXn5mZA"


def test_googledrivesource_make_address():
    assert (
        GoogleDriveSource(kind="file", google_id="an-id").make_address()
        == "gdrive://file/an-id"
    )
    assert (
        GoogleDriveSource(kind="folder", google_id="an-id").make_address()
        == "gdrive://folder/an-id"
    )


def test_googledrivesource_url():
    assert (
        GoogleDriveSource(kind="file", google_id="an-id").get_url()
        == "https://drive.google.com/file/d/an-id"
    )
    assert (
        GoogleDriveSource(kind="folder", google_id="an-id").get_url()
        == "https://drive.google.com/drive/folders/an-id"
    )


def test_googledrivesource_parse_address():
    for url in [
        "gdrive://file/1AkmcbU9uuEL9YBFsOXEP-LzORXsCGOIl",
        "drive.google.com/file/d/1AkmcbU9uuEL9YBFsOXEP-LzORXsCGOIl",
        "https://drive.google.com/file/d/1AkmcbU9uuEL9YBFsOXEP-LzORXsCGOIl",
        "https://drive.google.com/file/d/1AkmcbU9uuEL9YBFsOXEP-LzORXsCGOIl/view?usp=sharing",
    ]:
        sa = GoogleDriveSource.parse_address(url)
        assert sa.type == GoogleDriveSource
        assert sa.kind == "file"
        assert sa.google_id == "1AkmcbU9uuEL9YBFsOXEP-LzORXsCGOIl"

    for url in [
        "gdrive://folder/1OcB7VTWb3lc0u8FJX2LXc5GraKpn-r_m",
        "https://drive.google.com/drive/folders/1OcB7VTWb3lc0u8FJX2LXc5GraKpn-r_m",
        "https://drive.google.com/drive/u/1/folders/1OcB7VTWb3lc0u8FJX2LXc5GraKpn-r_m",
    ]:
        sa = GoogleDriveSource.parse_address(url)
        assert sa.type == GoogleDriveSource
        assert sa.kind == "folder"
        assert sa.google_id == "1OcB7VTWb3lc0u8FJX2LXc5GraKpn-r_m"

    # Use of strict
    assert GoogleDriveSource.parse_address("foo") is None
    with pytest.raises(ValidationError, match="Invalid Google Drive address"):
        GoogleDriveSource.parse_address("foo", strict=True)


@pytest.mark.django_db
def test_upload_source_pull():
    tier = AccountTier.objects.create()
    account = Account.objects.create(name="account-name", tier=tier)
    project = Project.objects.create(account=account, name="project-name")
    source = UploadSource.objects.create(project=project, file="some-file.txt")
    job = source.pull()
    params = job.params

    assert params["project"] == 1
    assert params["source"]["type"] == "Upload"
    assert params["source"]["path"].endswith("some-file.txt")


def test_urlsource_make_address():
    assert UrlSource(url="http://example.com").make_address() == "http://example.com"


def test_urlsource_url():
    assert UrlSource(url="http://example.com").get_url() == "http://example.com"


def test_urlsource_parse_address():
    assert UrlSource.parse_address("https://example.org") == SourceAddress(
        "Url", url="https://example.org"
    )

    assert UrlSource.parse_address("http://example.org/a-file.md") == SourceAddress(
        "Url", url="http://example.org/a-file.md"
    )

    assert UrlSource.parse_address("foo") is None
    assert UrlSource.parse_address("http://not-a-hostname") is None

    with pytest.raises(ValidationError, match="Invalid URL source"):
        UrlSource.parse_address("foo", strict=True)


class SourcesTests(DatabaseTestCase):
    def test_delete_project_with_source(self):
        """
        A regression test for https://github.com/stencila/hub/issues/754
        """
        account = Account.objects.create(name="test-account")
        project = Project.objects.create(account=account, name="test-project")
        ElifeSource.objects.create(project=project, article=5000, path="article.xml")
        project.delete()
