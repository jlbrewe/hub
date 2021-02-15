from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import select_template

from projects.api.views.files import ProjectsFilesViewSet
from projects.api.views.sources import ProjectsSourcesViewSet
from projects.models.sources import Source, UploadSource
from projects.ui.views.messages import all_messages
from users.socialaccount.tokens import get_user_google_token


def list(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    """Get a list of project sources."""
    viewset = ProjectsSourcesViewSet.init("list", request, args, kwargs)
    project = viewset.get_project()
    sources = viewset.get_queryset(project)

    all_messages(request, project)

    return render(
        request,
        "projects/sources/list.html",
        dict(sources=sources, project=project, meta=project.get_meta()),
    )


@login_required
def create(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    """
    Create a source.

    Looks for a template with name:

       projects/sources/create_<source-type>.html

    but falls back to using `projects/sources/create.html` with inclusion of:

       projects/sources/_create_<source-type>_fields.html

    falling back to:

       projects/sources/_create_fields.html
    """
    viewset = ProjectsSourcesViewSet.init("create", request, args, kwargs)

    source_type = kwargs.get("type")
    assert isinstance(source_type, str)
    source_class = Source.class_from_type_name(source_type).__name__

    template = select_template(
        [
            "projects/sources/create_{0}.html".format(source_type),
            "projects/sources/create.html",
        ]
    ).template.name
    fields_template = select_template(
        [
            "projects/sources/_create_{0}_fields.html".format(source_type),
            "projects/sources/_create_fields.html",
        ]
    ).template.name

    serializer_class = viewset.get_serializer_class(source_class=source_class)
    serializer = serializer_class()

    context = viewset.get_response_context(source_class=source_class)

    if source_class.startswith("Google"):
        token, app = get_user_google_token(request.user)
        if app:
            context["app_id"] = app.client_id.split("-")[0]
            context["client_id"] = app.client_id
            context["developer_key"] = settings.GOOGLE_API_KEY
        if token:
            context["access_token"] = token.token

    return render(
        request,
        template,
        dict(
            serializer=serializer,
            fields_template=fields_template,
            source_class=source_class,
            meta=context.get("project").get_meta(),
            **context
        ),
    )


@login_required
def upload(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    """
    Upload files to the project.

    If there is no existing `UploadSource` with the path, then one
    will be created. Otherwise the content of the source will be
    replaced with the uploaded content.
    """
    viewset = ProjectsSourcesViewSet.init("create", request, args, kwargs)
    project = viewset.get_project()

    if request.method == "GET":
        return render(
            request,
            "projects/sources/upload.html",
            dict(project=project, meta=project.get_meta()),
        )
    elif request.method == "POST":
        files = request.FILES.getlist("files")
        for file in files:
            source = UploadSource.create_or_update_from_uploaded_file(
                request.user, project, file.name, file
            )
        if len(files) == 1:
            return redirect(
                "ui-projects-sources-retrieve",
                project.account.name,
                project.name,
                source.id,
            )
        else:
            return redirect(
                "ui-projects-sources-list", project.account.name, project.name
            )
    else:
        raise Http404


def retrieve(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    """Retrieve a source."""
    viewset = ProjectsSourcesViewSet.init("retrieve", request, args, kwargs)
    project = viewset.get_project()
    source = viewset.get_object(project)

    viewset = ProjectsFilesViewSet.init("list", request, args, kwargs)
    files = viewset.get_queryset(project=project, source=source)
    context = viewset.get_response_context(queryset=files)

    return render(
        request,
        "projects/sources/retrieve.html",
        dict(source=source, meta=project.get_meta(), **context),
    )


@login_required
def update(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    """Update a source."""
    viewset = ProjectsSourcesViewSet.init("partial_update", request, args, kwargs)
    project = viewset.get_project()
    source = viewset.get_object(project)
    serializer = viewset.get_serializer(source)
    return render(
        request,
        "projects/sources/update.html",
        dict(serializer=serializer, source=source, meta=project.get_meta()),
    )


@login_required
def rename(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    """Rename (ie change the path of) a source."""
    viewset = ProjectsSourcesViewSet.init("partial_update", request, args, kwargs)
    project = viewset.get_project()
    source = viewset.get_object(project)
    serializer = viewset.get_serializer(source)
    return render(
        request,
        "projects/sources/rename.html",
        dict(
            serializer=serializer,
            source=source,
            project=project,
            account=project.account,
        ),
    )


@login_required
def destroy(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    """Destroy a source."""
    viewset = ProjectsSourcesViewSet.init("destroy", request, args, kwargs)
    project = viewset.get_project()
    source = viewset.get_object(project)
    return render(
        request,
        "projects/sources/destroy.html",
        dict(
            source=source,
            project=project,
            account=project.account,
            meta=project.get_meta(),
        ),
    )
