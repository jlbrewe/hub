from typing import Optional

from django.shortcuts import reverse
from rest_framework import exceptions, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.ui.views.content import snapshot_index_html
from jobs.api.helpers import redirect_to_job
from jobs.models import Job
from manager.api.authentication import (
    CsrfExemptSessionAuthentication,
    RefreshOAuthTokenAuthentication,
)
from manager.api.helpers import (
    HtmxCreateMixin,
    HtmxDestroyMixin,
    HtmxListMixin,
    HtmxRetrieveMixin,
)
from projects.api.serializers import SnapshotSerializer
from projects.api.views.projects import get_project
from projects.models.files import File
from projects.models.projects import Project, ProjectRole
from projects.models.snapshots import Snapshot
from users.models import AnonUser


class ProjectsSnapshotsViewSet(
    HtmxListMixin,
    HtmxCreateMixin,
    HtmxRetrieveMixin,
    HtmxDestroyMixin,
    viewsets.GenericViewSet,
):
    """A view set for project snapshots."""

    lookup_url_kwarg = "snapshot"
    object_name = "snapshot"
    queryset_name = "snapshots"

    authentication_classes = (
        CsrfExemptSessionAuthentication,
        RefreshOAuthTokenAuthentication,
    )

    def get_permissions(self):
        """
        Get the permissions that the current action requires.

        Override defaults so that `list`, `retrieve` etc do not require
        authentication (although they may raise permission denied
        if not a public project).
        """
        if self.action in ["list", "retrieve", "files", "archive", "session"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_project(self) -> Project:
        """
        Get the project for the current action and check user has roles.

        Mutating actions require that the user be an AUTHOR or above.
        """
        return get_project(
            self.kwargs,
            self.request.user,
            [
                ProjectRole.AUTHOR,
                ProjectRole.EDITOR,
                ProjectRole.MANAGER,
                ProjectRole.OWNER,
            ]
            if self.action in ["create", "partial_update", "destroy"]
            else [],
        )

    def get_queryset(self, project: Optional[Project] = None):
        """Get project snapshots."""
        project = project or self.get_project()
        queryset = (
            Snapshot.objects.filter(project=project)
            .order_by("-created")
            .select_related(
                "creator",
                "creator__personal_account",
                "project",
                "project__account",
                "job",
            )
        )
        return queryset

    def get_object(self, project: Optional[Project] = None) -> Snapshot:
        """Get a project snapshot."""
        try:
            return self.get_queryset(project).get(number=self.kwargs["snapshot"])
        except Snapshot.DoesNotExist:
            raise exceptions.NotFound

    def get_serializer_class(self):
        """Get the serializer class for the current action."""
        return SnapshotSerializer

    def get_success_url(self, serializer):
        """
        Get the URL to use in the Location header when an action is successful.

        For `create`, redirects to the page for the snapshot.
        """
        if self.action in ["create"]:
            snapshot = serializer.instance
            project = snapshot.project
            account = project.account
            return reverse(
                "ui-projects-snapshots-retrieve",
                args=[account.name, project.name, snapshot.number],
            )

    @action(detail=True, methods=["GET"], url_path="files/(?P<path>.*)")
    def files(self, request: Request, *args, **kwargs) -> Response:
        """
        Retrieve a file within a snapshot of the project.

        For `index.html` will add necessary headers and if necessary
        inject content required to connect to a session. For other files
        redirects to the URL for the file (which may be in a
        remote storage bucket for example).

        For security reasons, this function will be deprecated in
        favour of getting content from the account subdomain.
        """
        project = self.get_project()
        snapshot = self.get_object(project)
        path = self.kwargs.get("path") or "index.html"

        try:
            file = File.get_latest(snapshot=snapshot, path=path)
        except IndexError:
            raise exceptions.NotFound

        if path == "index.html":
            return snapshot_index_html(
                html=file.get_content(),
                request=request,
                account=project.account,
                project=project,
                snapshot=snapshot,
            )
        else:
            # Respond with the file directly
            return snapshot.file_response(path)

    @action(detail=True, methods=["get"])
    def archive(self, request: Request, *args, **kwargs) -> Response:
        """
        Retrieve an archive for a project snapshot.

        The user should have read access to the project.
        """
        snapshot = self.get_object()
        return snapshot.file_response(snapshot.zip_name)

    @action(detail=True, methods=["post"])
    def session(self, request: Request, *args, **kwargs) -> Response:
        """
        Get a session for the snapshot.

        If the user has already created, or is connected to,
        a `session` job for this snapshot, and that job is still running,
        then returns that job. Otherwise, creates a new session.
        """
        snapshot = self.get_object()
        try:
            job = Job.objects.filter(
                snapshot=snapshot,
                is_active=True,
                **(
                    {"users": request.user}
                    if request.user.is_authenticated
                    else {"anon_users__id": AnonUser.get_id(request)}
                )
            ).order_by("-created")[0]
        except IndexError:
            job = snapshot.session(request)
            job.dispatch()

        return redirect_to_job(job)
