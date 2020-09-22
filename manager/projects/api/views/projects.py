from typing import Dict, List, Optional

from django.db.models import Q
from django.db.models.expressions import RawSQL
from django.shortcuts import reverse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import exceptions, permissions, throttling, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from jobs.api.helpers import redirect_to_job
from manager.api.helpers import (
    HtmxCreateMixin,
    HtmxDestroyMixin,
    HtmxListMixin,
    HtmxRetrieveMixin,
    HtmxUpdateMixin,
    filter_from_ident,
)
from projects.api.serializers import (
    ProjectAgentCreateSerializer,
    ProjectAgentSerializer,
    ProjectAgentUpdateSerializer,
    ProjectCreateSerializer,
    ProjectDestroySerializer,
    ProjectListSerializer,
    ProjectRetrieveSerializer,
    ProjectUpdateSerializer,
)
from projects.models.projects import Project, ProjectAgent, ProjectRole
from projects.models.sources import Source
from users.models import User


def get_projects(user: User):
    """
    Get a queryset of projects for the user.

    For authenticated users, each project is annotated with the
    role of the user for the project.
    """
    if user.is_authenticated:
        # Annotate the queryset with the role of the user
        # Role is the "greater" of the project role and the
        # account role (for the account that owns the project).
        # Authenticated users can see public projects and those in
        # which they have a role
        return Project.objects.annotate(
            role=RawSQL(
                """
SELECT
CASE account_role.role
WHEN 'OWNER' THEN 'OWNER'
WHEN 'MANAGER' THEN
    CASE project_role.role
    WHEN 'OWNER' THEN 'OWNER'
    ELSE 'MANAGER' END
ELSE project_role.role END AS "role"
FROM projects_project AS project
LEFT JOIN
    (SELECT project_id, "role" FROM projects_projectagent WHERE user_id = %s) AS project_role
    ON project.id = project_role.project_id
LEFT JOIN
    (SELECT account_id, "role" FROM accounts_accountuser WHERE user_id = %s) AS account_role
    ON project.account_id = account_role.account_id
WHERE project.id = projects_project.id""",
                [user.id, user.id],
            )
        ).filter(Q(public=True) | Q(role__isnull=False))
    else:
        # Unauthenticated users can only see public projects
        return Project.objects.filter(public=True).extra(select={"role": "NULL"})


def get_project(
    identifiers: Dict[str, str], user: User, roles: Optional[List[ProjectRole]] = None,
):
    """
    Get a project for the user, optionally requiring one or more roles.

    Like GitHub, raises a `NotFound` exception if the user does not have permission
    to avoid leaking the existence of a private project.
    """
    filter = filter_from_ident(identifiers["project"])

    account = identifiers.get("account")
    if account:
        filter.update(**filter_from_ident(account, prefix="account"))
    elif "id" not in filter:
        filter.update({"account__name": "temp"})

    try:
        return get_projects(user).get(
            **filter, **(dict(role__in=[role.name for role in roles]) if roles else {}),
        )
    except Project.DoesNotExist:
        raise exceptions.NotFound


class ProjectsCreateAnonThrottle(throttling.AnonRateThrottle):
    """
    Throttle for temporary project creation by anonymous users.
    """

    rate = "10/day"


class ProjectsViewSet(
    HtmxListMixin,
    HtmxCreateMixin,
    HtmxRetrieveMixin,
    HtmxUpdateMixin,
    HtmxDestroyMixin,
    viewsets.GenericViewSet,
):
    """
    A view set for projects.

    Provides basic CRUD views for projects.
    """

    lookup_url_kwarg = "project"
    object_name = "project"
    queryset_name = "projects"

    def get_permissions(self):
        """
        Get the permissions that the current action requires.

        Override defaults so that, `create`, `list` and `retrive` do not require
        authentication (although other restrictions do apply for anon users).
        """
        if self.action in ["create", "list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_throttles(self):
        """
        Get the throttles to apply to the current request.
        """
        if self.action == "create" and self.request.user.is_anonymous:
            return [ProjectsCreateAnonThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        """
        Get the set of projects that the user has access to and which meet filter criteria.

        Does not return temporary projects.

        TODO: Currently this ignores an authenticated user's access to
              projects inherited from membership of a team.
        """
        queryset = get_projects(self.request.user).select_related("account")

        account = self.request.GET.get("account")
        if account:
            queryset = queryset.filter(account_id=account)

        role = self.request.GET.get("role")
        if self.request.user.is_authenticated and role:
            if role.lower() == "member":
                queryset = queryset.filter(role__isnull=False)
            else:
                try:
                    project_role = ProjectRole.from_string(role)
                except ValueError as exc:
                    raise exceptions.ValidationError({"role": str(exc)})
                else:
                    queryset = queryset.filter(role=project_role.name)

        public = self.request.GET.get("public")
        if public:
            if public.lower() in ["false", "no", "0"]:
                queryset = queryset.filter(public=False)
            else:
                queryset = queryset.filter(public=True)

        source = self.request.GET.get("source")
        if source:
            try:
                query = Source.query_from_address(source, prefix="sources")
            except ValueError as exc:
                raise exceptions.ValidationError({"source": str(exc)})
            else:
                print(query)
                queryset = queryset.filter(query)

        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(title__icontains=search)
                | Q(description__icontains=search)
            )

        return queryset.filter(temporary=False).order_by("-role")

    def get_object(self):
        """
        Get the project.

        Read access control is done in the `get_project` function.
        For `partial-update` and `destroy` does an additional
        check that the user is a project MANAGER and/or OWNER.

        For temporary projects, ensure that the project was accessed
        by it's name, not it's id (this prevent access to a
        temporary project by guessing it's integer id).
        Because temporary objects do not have any users with roles,
        anyone with their name can modify or delete them.
        """
        project = get_project(self.kwargs, self.request.user)

        if project.temporary is True:
            if "name" not in filter_from_ident(self.kwargs["project"]):
                raise exceptions.NotFound
            return project

        if (
            self.action == "partial_update"
            and project.role not in [ProjectRole.MANAGER.name, ProjectRole.OWNER.name]
        ) or (self.action == "destroy" and project.role != ProjectRole.OWNER.name):
            raise exceptions.PermissionDenied

        return project

    def get_serializer_class(self):
        """Get the serializer class for the current action."""
        try:
            return {
                "list": ProjectListSerializer,
                "create": ProjectCreateSerializer,
                "retrieve": ProjectRetrieveSerializer,
                "partial_update": ProjectUpdateSerializer,
                "destroy": ProjectDestroySerializer,
            }[self.action]
        except KeyError:
            raise RuntimeError("Unexpected action {}".format(self.action))

    def get_success_url(self, serializer):
        """
        Get the URL to use in the Location header when an action is successful.

        For `create`, redirects to the "main" page for the project.
        """
        if self.action in ["create", "partial_update"]:
            project = serializer.instance
            return reverse(
                "ui-projects-retrieve", args=[project.account.name, project.name]
            )
        else:
            return None

    # Most of the following views serve simply to provide docstrings
    # from which API documentation is generated.

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "account",
                openapi.IN_QUERY,
                description="The integer of the id of the account that the project belongs to.",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "role",
                openapi.IN_QUERY,
                description="The role that the currently authenticated user has on the project "
                'e.g. "editor", "owner" (for any role, use "member")',
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "public",
                openapi.IN_QUERY,
                description="Whether or not the project is public.",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="A string to search for in the project `name`, `title` or `description`.",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "source",
                openapi.IN_QUERY,
                description="The address of a project source e.g. `github://<org>/<repo>`, `gdoc://<id>`.",
                type=openapi.TYPE_STRING,
            ),
        ]
    )
    def list(self, request: Request, *args, **kwargs) -> Response:
        """
        List projects.

        Returns a list of projects that are accessible to the user, including those that are
        public and those that the user is a member of (i.e. has a project role for).

        The returned list can be filtered using query parameters, `account`, `role`, `public`,
        `search`, `source`. The `role` filter applies to the currently authenticated user, and
        as such has no effected for unauthenticated requests.

        For example, to list all projects for which the authenticated user is a member and which
        uses a particular Google Doc as a source:

            GET /projects?role=member&source=gdoc://1BW6MubIyDirCGW9Wq-tSqCma8pioxBI6VpeLyXn5mZA
        """
        return super().list(request, *args, **kwargs)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """
        Create a project.

        Receives details of the project.
        Returns details of the new project.
        """
        return super().create(request, *args, **kwargs)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        """
        Retrieve a project.

        Returns details of the project.
        """
        return super().retrieve(request, *args, **kwargs)

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        """
        Update a project.

        Receives details of the project.
        Returns updated details of the project.
        """
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """
        Destroy a project.

        Returns an empty response on success.
        """
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["POST"])
    def pull(self, request: Request, *args, **kwargs) -> Response:
        """
        Pull the project.

        Creates a pull job and redirects to it.
        """
        project = self.get_object()
        job = project.pull(request.user)
        job.dispatch()
        return redirect_to_job(job, accepts_html=self.accepts_html())


class ProjectsAgentsViewSet(
    HtmxListMixin,
    HtmxCreateMixin,
    HtmxRetrieveMixin,
    HtmxUpdateMixin,
    HtmxDestroyMixin,
    viewsets.GenericViewSet,
):
    """
    A view set for projects agents (users or teams).

    Provides basic CRUD views for project agents.

    Uses `ProjectsViewSet.get_object` so that we can obtain the
    role of the user for the project (including inherited role from the account).
    """

    lookup_url_kwarg = "agent"
    object_name = "agent"
    queryset_name = "agents"

    def get_project(self) -> Project:
        """Get the project and check that the user has permission to the perform action."""
        project = ProjectsViewSet.init(
            self.action, self.request, self.args, self.kwargs
        ).get_object()

        if (
            self.action in ["create", "partial_update", "destroy"]
            and project.role not in [ProjectRole.MANAGER.name, ProjectRole.OWNER.name]
        ) or project.role is None:
            raise exceptions.PermissionDenied

        return project

    def get_queryset(self):
        """Get project agents."""
        project = self.get_project()
        return ProjectAgent.objects.filter(project=project)

    def get_object(self) -> ProjectAgent:
        """Get a project agent."""
        try:
            return self.get_queryset().filter(id=self.kwargs["agent"])[0]
        except IndexError:
            raise exceptions.NotFound

    def get_serializer_class(self):
        """Get the serializer class for the current action."""
        if self.action == "create":
            # Call `get_project` to perform permission check
            self.get_project()
            return ProjectAgentCreateSerializer
        elif self.action == "partial_update":
            return ProjectAgentUpdateSerializer
        elif self.action == "destroy":
            return None
        else:
            return ProjectAgentSerializer

    def get_response_context(self, **kwargs):
        """Override to provide additional context when rendering templates."""
        return super().get_response_context(
            queryset=self.get_queryset(), project=self.get_project(), **kwargs
        )
