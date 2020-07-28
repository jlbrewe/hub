import re

import shortuuid
from django.db.models import Q
from rest_framework import exceptions, serializers
from rest_polymorphic.serializers import PolymorphicSerializer

from accounts.api.serializers import AccountListSerializer
from accounts.models import Account, AccountTeam, AccountUser
from accounts.paths import AccountPaths
from accounts.quotas import AccountQuotas
from manager.api.exceptions import AccountQuotaExceeded
from manager.api.helpers import get_help_text, get_object_from_ident
from manager.api.validators import FromContextDefault
from manager.helpers import unique_slugify
from manager.themes import Themes
from projects.models.files import File
from projects.models.projects import Project, ProjectAgent, ProjectRole
from projects.models.snapshots import Snapshot
from projects.models.sources import (
    ElifeSource,
    GithubSource,
    GoogleDocsSource,
    GoogleDriveSource,
    PlosSource,
    Source,
    UploadSource,
    UrlSource,
)
from users.models import User


class ProjectAgentSerializer(serializers.ModelSerializer):
    """
    A serializer for project agents.

    Translates the `user` and `team` fields into
    `type` and `agent` (an id).
    """

    type = serializers.SerializerMethodField()

    agent = serializers.SerializerMethodField()

    class Meta:
        model = ProjectAgent
        fields = ["id", "project", "type", "agent", "role"]

    def get_type(self, instance):  # noqa: D102
        if instance.user:
            return "user"
        if instance.team:
            return "team"

    def get_agent(self, instance):  # noqa: D102
        if instance.user:
            return instance.user.id
        if instance.team:
            return instance.team.id


class ProjectAgentCreateSerializer(ProjectAgentSerializer):
    """
    A serializer for adding project agents.

    Includes an hidden field for the `project` and restricts
    the choices for `role`.
    """

    project = serializers.HiddenField(
        default=FromContextDefault(
            lambda context: get_object_from_ident(
                Project, context["view"].kwargs["project"]
            )
        )
    )

    type = serializers.ChoiceField(choices=["user", "team"], write_only=True)

    agent = serializers.IntegerField(write_only=True)

    role = serializers.ChoiceField(choices=[role.name for role in ProjectRole])

    def validate(self, data):
        """
        Validate the data.

        - valid user or team id
        - no existing role for the agent
        """
        if data["type"] == "user":
            if User.objects.filter(id=data["agent"]).count() == 0:
                raise exceptions.ValidationError(
                    {"agent": "User with id {0} does not exist.".format(data["agent"])}
                )
        elif data["type"] == "team":
            if AccountTeam.objects.filter(id=data["agent"]).count() == 0:
                raise exceptions.ValidationError(
                    {"agent": "Team with id {0} does not exist.".format(data["agent"])}
                )

        if (
            ProjectAgent.objects.filter(
                Q(user_id=data["agent"]) | Q(team_id=data["agent"]),
                project=data["project"],
            ).count()
            > 0
        ):
            raise exceptions.ValidationError({"agent": "Already has a project role."})

        return data

    def create(self, validated_data):
        """Create the project agent."""
        return ProjectAgent.objects.create(
            project=validated_data["project"],
            user_id=validated_data["agent"]
            if validated_data["type"] == "user"
            else None,
            team_id=validated_data["agent"]
            if validated_data["type"] == "team"
            else None,
            role=validated_data["role"],
        )


class ProjectAgentUpdateSerializer(serializers.ModelSerializer):
    """
    A serializer for updating project agents.

    Only allows changing the `role` field (do not
    want to allow changing to a different project for example).
    """

    class Meta:
        model = ProjectAgent
        fields = "__all__"
        read_only_fields = ["id", "project", "user", "team"]


class ProjectAccountField(serializers.PrimaryKeyRelatedField):
    """
    Field for a project account.

    Limits the set of valid accounts for a project to those that
    the user is a member of.  Sets the default to the name in the query (if any).
    Will raise a validation error e.g. "Invalid pk "42" - object does not exist."
    if the user is not a member of the account.
    """

    def get_queryset(self):
        """
        Get the list of accounts the user is a member of.
        """
        request = self.context.get("request", None)
        if request is None:
            return Account.objects.none()

        queryset = Account.objects.filter(users__user=request.user)

        name = request.GET.get("account")
        if name:
            queryset = queryset.filter(name=name)

        return queryset


class ProjectSerializer(serializers.ModelSerializer):
    """
    Base serializer for projects.

    Uses `ProjectAccountField` to limit the accounts that are listed
    or can own the project. Uses a `ChoiceField` for theme to limit the theme
    name to those currently provided by Thema.
    """

    account = ProjectAccountField(
        default=None, help_text=get_help_text(Project, "account")
    )

    theme = serializers.ChoiceField(
        choices=Themes.as_choices(),
        allow_blank=True,
        required=False,
        help_text=get_help_text(Project, "theme"),
    )

    class Meta:
        model = Project
        fields = [
            "id",
            "account",
            "creator",
            "created",
            "name",
            "title",
            "description",
            "temporary",
            "public",
            "main",
            "theme",
        ]

    def validate_ownership_by_account(self, public: bool, account: Account):
        """
        Validate that a project can be be owned by an account by checking quotas are not exceeded.
        """
        try:
            if public:
                AccountQuotas.PROJECTS_PUBLIC.check(account)
            else:
                AccountQuotas.PROJECTS_PRIVATE.check(account)
        except AccountQuotaExceeded as exc:
            raise exceptions.ValidationError(
                dict(public=list(exc.detail.values()).pop() or "Account quota exceeded")
            )

    def validate_name_for_account(self, name: str, account: Account):
        """
        Validate that the name if valid for the account.

        Used below by `ProjectCreateSerializer` and `ProjectUpdateSerializer`.
        """
        if AccountPaths.has(name):
            raise exceptions.ValidationError(
                dict(name="Project name '{0}' is unavailable.".format(name))
            )

        if (
            Project.objects.filter(account=account, name=name)
            .exclude(id=self.instance.id if self.instance else None)
            .count()
        ):
            raise exceptions.ValidationError(
                dict(
                    name="Project name '{0}' is already in use for this account.".format(
                        name
                    )
                )
            )

        name = unique_slugify(
            name,
            instance=self.instance,
            queryset=Project.objects.filter(account=account),
        )

        MIN_LENGTH = 3
        if len(name) < MIN_LENGTH:
            raise exceptions.ValidationError(
                dict(
                    name="Project name must have at least {0} valid characters.".format(
                        MIN_LENGTH
                    )
                )
            )

        MAX_LENGTH = 64
        if len(name) > MAX_LENGTH:
            raise exceptions.ValidationError(
                dict(
                    name="Project name must be less than {0} characters long.".format(
                        MAX_LENGTH
                    )
                )
            )

        return name


class ProjectListSerializer(ProjectSerializer):
    """
    Serializer for listing projects.

    Includes the role of the user making the request.
    """

    role = serializers.CharField(
        read_only=True, help_text="Role of the current user on the project (if any)."
    )

    account = AccountListSerializer()

    class Meta:
        model = Project
        fields = ProjectSerializer.Meta.fields + ["role"]


class ProjectCreateSerializer(ProjectSerializer):
    """
    Serializer for creating a project.

    Set's the request user as the project `creator`.
    Allows for the `name` field to be empty for temporary projects.
    """

    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())

    name = serializers.CharField(default=None, help_text=get_help_text(Project, "name"))

    class Meta:
        model = Project
        fields = ProjectSerializer.Meta.fields

    def validate(self, data):
        """
        Validate the project creation fields.

        If the user is unauthenticated, creates a temporary project.

        If the user is authenticated. Checks that the user is a member of
        the specified account and that the account has sufficient quotas to
        create the project.
        """
        request = self.context.get("request")
        account = data.get("account")

        # Set the creator to null if the user is anon
        if request.user.is_anonymous:
            data["creator"] = None

        # Ensure that if the user is anonymous, or the account is
        # not specified that the project is marked as temporary and public
        # and has a random, very difficult to guess name that won't clash with
        # an existing temp project.
        # No need for any more validation so just return the data after that.
        if request.user.is_anonymous or account is None:
            data["account"] = Account.get_temp_account()
            data["temporary"] = True
            data["public"] = True
            data["name"] = shortuuid.uuid()
            return data

        # Check that user is an account member.
        # This should already done by `ProjectAccountField.get_queryset` but
        # this is a further check
        if AccountUser.objects.filter(account=account, user=request.user).count() == 0:
            raise exceptions.ValidationError(
                dict(account="You are not a member of this account")
            )

        # Default to public project and check against account quotas
        data["public"] = public = data.get("public", True)
        self.validate_ownership_by_account(public, account)

        # Check that name is valid
        data["name"] = self.validate_name_for_account(data.get("name", ""), account)

        return data


ProjectRetrieveSerializer = ProjectSerializer


class ProjectUpdateSerializer(ProjectSerializer):
    """
    Serializer for updating a project.
    """

    class Meta:
        model = Project
        fields = ProjectSerializer.Meta.fields

    def validate(self, data):
        """
        Validate the project's fields.
        """
        request = self.context.get("request")
        project = self.instance

        # If changing from temporary to non-temporary we need
        # to ensure that the current user is made a owner (if they are not already)
        if project.temporary and data.get("temporary") is False:
            ProjectAgent.objects.get_or_create(
                project=project, user=request.user, role=ProjectRole.OWNER.name
            )

        # Otherwise if changing the account...
        elif data.get("account") is not None:
            # Check that the user is a project owner
            try:
                ProjectAgent.objects.get(
                    project=project, user=request.user, role=ProjectRole.OWNER.name
                )
            except ProjectAgent.DoesNotExist:
                raise exceptions.ValidationError(
                    dict("Only a project owner can change it's account.")
                )

            account = data.get("account")

            # Check that user is an account member.
            # This should already done by `ProjectAccountField.get_queryset` but
            # this is a further check
            if (
                AccountUser.objects.filter(account=account, user=request.user).count()
                == 0
            ):
                raise exceptions.ValidationError(
                    dict(account="You are not a member of this account")
                )

            # Check that the new account has enough quota to own account
            self.validate_ownership_by_account(data.get("public", True), account)

        # Otherwise, if changing from public to private then check against the account quota.
        # Note that this allows an existing project to be made public even if that
        # will exceed the quota
        elif project.public and data.get("public") is False:
            self.validate_ownership_by_account(False, project.account)

        # Check the new name is valid for this account
        name = data.get("name")
        if name is not None:
            data["name"] = self.validate_name_for_account(name, project.account)

        return data


class ProjectDestroySerializer(serializers.Serializer):
    """
    Serializer for destroying a project.

    Requires the `name` of the project as confirmation that the user
    really wants to destroy it.
    """

    name = serializers.CharField(
        help_text="Confirm by providing the name of the project to be destroyed."
    )

    def validate_name(self, value):
        """Validate that the provided name matches."""
        if value != self.instance.name:
            raise exceptions.ValidationError(
                "Provided name does not match the project name."
            )


class FileSerializer(serializers.ModelSerializer):
    """
    Serializer for a file.
    """

    project = serializers.HiddenField(
        default=FromContextDefault(
            lambda context: get_object_from_ident(
                Project, context["view"].kwargs["project"]
            )
        )
    )

    class Meta:
        model = File
        fields = "__all__"


class FileListSerializer(FileSerializer):
    """
    Serializer for a file.
    """

    # These fields are calculated in `get_queryset`
    # (e.g. for aggregation by directory)

    name = serializers.SerializerMethodField()
    is_directory = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()

    def get_name(self, obj) -> str:
        """Get the name of the file / dir."""
        return str(obj.get("name")) if isinstance(obj, dict) else obj.name

    def get_is_directory(self, obj) -> bool:
        """Is the entry a directory."""
        return bool(obj.get("is_directory")) if isinstance(obj, dict) else False

    def get_count(self, obj) -> int:
        """Get the number of files in a dir."""
        return int(str(obj.get("count"))) if isinstance(obj, dict) else 1

    def get_source(self, obj):
        """Get the list of sources. Always just a single source for a file."""
        if isinstance(obj, dict):
            return [source.id for source in obj["source"]]
        else:
            return [obj.source and obj.source.id]


class SnapshotSerializer(serializers.ModelSerializer):
    """
    A serializer for snapshots.
    """

    project = serializers.HiddenField(
        default=FromContextDefault(
            lambda context: get_object_from_ident(
                Project, context["view"].kwargs["project"]
            )
        )
    )

    class Meta:
        model = Snapshot
        fields = "__all__"
        read_only_fields = ["id", "project", "number", "creator", "created", "job"]

    def create(self, validated_data):
        """
        Create a new snapshot for a project.
        """
        project = validated_data.get("project")
        assert project is not None

        request = self.context.get("request")
        assert request is not None

        return Snapshot.create(project, request.user)


class SourceSerializer(serializers.ModelSerializer):
    """
    Base serializer for source instances.

    Project is read only to prevent a change to another
    project for which the user does not have permissions.
    """

    project = serializers.HiddenField(
        default=FromContextDefault(
            lambda context: get_object_from_ident(
                Project, context["view"].kwargs["project"]
            )
        )
    )

    type = serializers.SerializerMethodField()

    class Meta:
        model = Source
        exclude = ["polymorphic_ctype", "jobs"]
        read_only_fields = [
            "project",
            "address",
            "creator",
            "created",
            "updated",
            "jobs",
        ]

    def get_type(self, source: Source):
        """
        Get the name of the class of the source.

        This is intended to match the `type` field
        of the `PolymorphicSourceSerializer`.
        """
        return source.type_class

    def validate_path(self, value):
        """
        Validate the path field.

        Splits into parts and checks that it each part only contains valid
        characters.
        """
        for part in value.split("/"):
            match = re.search(r"^[A-Za-z][A-Za-z0-9\.\-_ ]*$", part, re.I)
            if not match:
                raise exceptions.ValidationError(
                    'Path contains an invalid part: "{0}"'.format(part)
                )
        return value

    def skip_validate(self, data):
        """
        Validate that the source does not yet exist for the project.
        """
        project = data.get("project", self.instance.project if self.instance else None)
        address = Source(**data).make_address()
        id = self.instance.id if self.instance else None

        if (
            Source.objects.filter(project=project, address=address)
            .exclude(id=id)
            .count()
        ):
            raise exceptions.ValidationError(
                # For now, we need to associate this error with path, because
                # it is always in the form.
                dict(path="This source is already linked into this project.")
            )
        return data

    def create(self, *args, **kwargs):
        """
        Override to pull the source after it has been created.
        """
        source = super().create(*args, **kwargs)
        job = source.pull()
        job.dispatch()
        return source


class ElifeSourceSerializer(SourceSerializer):
    """
    Serializer for eLife sources.
    """

    class Meta:
        model = ElifeSource
        fields = "__all__"
        read_only_fields = SourceSerializer.Meta.read_only_fields


class GithubSourceSerializer(SourceSerializer):
    """
    Serializer for GitHub sources.
    """

    url = serializers.CharField(
        required=False, allow_blank=True, help_text="The URL of the repository."
    )

    repo = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="A GitHub repository name (e.g. org/name).",
    )

    class Meta:
        model = GithubSource
        fields = "__all__"
        read_only_fields = SourceSerializer.Meta.read_only_fields

    def validate(self, data):
        """
        Validate the url field.
        """
        url = data.get("url")
        repo = data.get("repo")
        if url:
            address = GithubSource.parse_address(url, strict=True)
            del data["url"]
            data["repo"] = address.repo
            data["subpath"] = address.subpath
            return data
        elif repo:
            if not re.match(r"^(?:[a-z0-9\-]+)/(?:[a-z0-9\-_]+)$"):
                raise exceptions.ValidationError(
                    dict(repo="Not a valid GitHub repository name.")
                )
            return data
        else:
            raise exceptions.ValidationError(
                dict(
                    url="Please provide either a GitHub URL or a GitHub repository name."
                )
            )

        return super.validate()


class GoogleDocsSourceSerializer(SourceSerializer):
    """
    Serializer for Google Docs sources.
    """

    doc_id = serializers.CharField(
        help_text="A Google Doc id e.g. 1iNeKTbnIcW_92Hmc8qxMkrW2jPrvwjHuANju2hkaYkA, or its "
        "URL e.g https://docs.google.com/document/d/1iNeKTbnIcW_92Hmc8qxMkrW2jPrvwjHuANju2hkaYkA/edit"
    )

    class Meta:
        model = GoogleDocsSource
        fields = "__all__"
        read_only_fields = SourceSerializer.Meta.read_only_fields

    def validate_doc_id(self, value):
        """
        Validate the document id.
        """
        return GoogleDocsSource.parse_address(value, naked=True, strict=True).doc_id


class GoogleDriveSourceSerializer(SourceSerializer):
    """
    Serializer for Google Drive sources.
    """

    class Meta:
        model = GoogleDriveSource
        fields = "__all__"
        read_only_fields = SourceSerializer.Meta.read_only_fields


class PlosSourceSerializer(SourceSerializer):
    """
    Serializer for PLOS sources.
    """

    class Meta:
        model = PlosSource
        fields = "__all__"
        read_only_fields = SourceSerializer.Meta.read_only_fields


class UploadSourceSerializer(SourceSerializer):
    """
    Serializer for uploaded sources.
    """

    class Meta:
        model = UploadSource
        fields = "__all__"
        read_only_fields = SourceSerializer.Meta.read_only_fields


class UrlSourceSerializer(SourceSerializer):
    """
    Serializer for URL sources.
    """

    class Meta:
        model = UrlSource
        fields = "__all__"
        read_only_fields = SourceSerializer.Meta.read_only_fields


class SourcePolymorphicSerializer(PolymorphicSerializer):
    """
    Serializer which dispatches to the appropriate serializer depending upon source type.
    """

    resource_type_field_name = "type"

    model_serializer_mapping = {
        Source: SourceSerializer,
        ElifeSource: ElifeSourceSerializer,
        GithubSource: GithubSourceSerializer,
        GoogleDocsSource: GoogleDocsSourceSerializer,
        GoogleDriveSource: GoogleDriveSourceSerializer,
        PlosSource: PlosSourceSerializer,
        UploadSource: UploadSourceSerializer,
        UrlSource: UrlSourceSerializer,
    }

    class_name_serializer_mapping = dict(
        [
            (model.__name__, serializer)
            for model, serializer in model_serializer_mapping.items()
        ]
    )
