import re
from typing import Optional

import httpx
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse

from accounts.models import Account
from jobs.models import JobStatus
from projects.models.files import File
from projects.models.projects import Project, ProjectLiveness
from projects.models.snapshots import Snapshot

storage_client = httpx.Client()


def content(
    request: HttpRequest,
    project_name: Optional[str] = None,
    version: Optional[str] = None,
    file_path: Optional[str] = None,
) -> HttpResponse:
    """
    Serve content on behalf on an account.

    This view is designed to handle all the serving of account content.
    It's the Hub's equivalent of Github Pages which serves content from
    https://<account>.stencila.io/<project>.
    """
    host = request.get_host()
    print(host)
    if (
        settings.CONFIGURATION.endswith("Dev")
        or settings.CONFIGURATION.endswith("Test")
    ) and (host.startswith("127.0.0.1") or host.startswith("localhost")):
        # During development and testing get the account name
        # from a URL parameter
        account_name = request.GET.get("account")
        assert account_name is not None, "Do you need to add `?=account` to URL?"
    else:
        # In production get the account from the request subdomain
        match = re.match(r"^([^.]+)." + settings.ACCOUNTS_DOMAIN, host)

        # Assert that this is NOT the primary domain (we never want to
        # serve account content from there)
        assert match is not None
        assert settings.PRIMARY_DOMAIN not in host

        account_name = match.group(1)

    # Get the account
    account = get_object_or_404(Account, name=account_name)

    # If no project is specified then redirect to the account's page
    # on the Hub (rather than 404ing).
    # In the future we may allow accounts to specify a default project
    # to serve as a "home" project.
    if not project_name:
        return redirect(
            "{scheme}://{domain}:{port}/{account}".format(
                scheme="https" if request.is_secure() else "http",
                domain=settings.PRIMARY_DOMAIN,
                port=request.get_port(),
                account=account,
            )
        )

    def unavailable_project():
        return render(
            request,
            "accounts/content/404_unavailable_project.html",
            dict(account=account, project_name=project_name),
            status=404,
        )

    # Check for project
    try:
        project = Project.objects.get(account=account, name=project_name)
    except Project.DoesNotExist:
        return unavailable_project()

    # Authorize the request
    # This is being served on a domain where we do not know the user.
    # So if the project is not public then a key must be provided in the URL
    if not project.public:
        key = request.GET.get("key")
        if key != project.key:
            return unavailable_project()

    # If the URL does not have an explicit version then fallback to project defaults
    if version is None:
        version = project.liveness

    # Which snapshot or working directory to serve from?
    if version == ProjectLiveness.LATEST.value:
        snapshots = project.snapshots.filter(
            job__status=JobStatus.SUCCESS.value
        ).order_by("-created")
        if snapshots:
            snapshot = snapshots[0]
        else:
            return render(
                request,
                "accounts/content/404_no_snapshots.html",
                dict(account=account, project=project),
                status=404,
            )
    elif version == ProjectLiveness.PINNED.value:
        # Elsewhere there should be checks to ensure the data
        # does not break the following asserts. But these serve as
        # a final check.
        snapshot = project.pinned
        assert (
            snapshot is not None
        ), "Project has liveness `pinned` but is not pinned to a snapshot"
        assert (
            snapshot.project_id == project.id
        ), "Project is pinned to a snapshot for a different project!"
    elif version.startswith("v"):
        match = re.match(r"v(\d+)$", version)
        if match is None:
            return render(
                request, "accounts/content/404_invalid_snapshot.html", status=404
            )
        number = match.group(1)
        try:
            snapshot = Snapshot.objects.get(project=project, number=number)
        except Snapshot.DoesNotExist:
            return render(
                request, "accounts/content/404_invalid_snapshot.html", status=404
            )
    else:
        raise ValueError("Invalid version value: " + version)

    # Default to serving index.html
    if not file_path:
        file_path = "index.html"

    # Check that the file exists in the snapshot
    # Is DB query necessary, or can we simply rely on upstream 404ing ?
    get_object_or_404(File, snapshot=snapshot, path=file_path)

    # Handle the index.html file specially
    if file_path == "index.html":
        return snapshot_index_html(account=account, project=project, snapshot=snapshot)

    # Redirect to other files
    url = snapshot.file_url(file_path)
    if settings.CONFIGURATION.endswith("Dev"):
        # During development just do a simple redirect
        return redirect(url)
    else:
        # In production, send the the `X-Accel-Redirect` and other headers
        # so that Nginx will reverse proxy
        response = HttpResponse()
        response["X-Accel-Redirect"] = "@account-content"
        response["X-Accel-Redirect-URL"] = url
        return response


def snapshot_index_html(
    account: Account, project: Project, snapshot: Snapshot
) -> HttpResponse:
    """
    Return a snapshot's index.html.

    Adds necessary headers and injects content
    required to connect to a session.
    """
    if isinstance(snapshot.STORAGE, FileSystemStorage):
        # Serve the file from the filesystem.
        # Normally this will only be used during development!
        location = snapshot.file_location("index.html")
        with snapshot.STORAGE.open(location) as file:
            html = file.read()
    else:
        # Fetch the file from storage and send it on to the client
        url = snapshot.file_url("index.html")
        html = storage_client.get(url).content

    if not html:
        raise RuntimeError("No content")

    # Inject execution toolbar
    source_url = reverse(
        "ui-projects-snapshots-retrieve",
        kwargs=dict(
            account=account.name, project=project.name, snapshot=snapshot.number,
        ),
    )
    session_provider_url = reverse(
        "api-projects-snapshots-session",
        kwargs=dict(project=project.id, snapshot=snapshot.number),
    )
    toolbar = """
        <stencila-executable-document-toolbar
            source-url="{source_url}"
            session-provider-url="{session_provider_url}"
        >
        </stencila-executable-document-toolbar>
    """.format(
        source_url=source_url, session_provider_url=session_provider_url
    )
    html = html.replace(
        b'data-itemscope="root">', b'data-itemscope="root">' + toolbar.encode()
    )

    response = HttpResponse(html)

    # Add headers if the account has `hosts` set
    hosts = account.hosts
    if hosts:
        # CSP `frame-ancestors` for modern browers
        response["Content-Security-Policy"] = "frame-ancestors 'self' {};".format(hosts)
        # `X-Frame-Options` for older browsers (only allows one value)
        host = hosts.split()[0]
        response["X-Frame-Options"] = "allow-from {}".format(host)
    else:
        response["Content-Security-Policy"] = "frame-ancestors 'self';"
        response["X-Frame-Options"] = "sameorigin"

    return response
