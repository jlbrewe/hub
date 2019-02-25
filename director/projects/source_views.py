import os
import typing

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView

from lib.github_facade import user_github_token
from projects.permission_models import ProjectPermissionType
from projects.project_views import ProjectPermissionsMixin
from projects.source_edit import SourceEditContext, SourceContentFacade
from projects.source_models import LinkedSourceAuthentication, DiskFileSource
from projects.source_operations import strip_directory, get_filesystem_project_path, utf8_path_join
from .models import Project, Source, FileSource, DropboxSource, GithubSource
from .source_forms import GithubSourceForm, SourceUpdateForm, RelativeFileSourceForm


class SourceCreateView(LoginRequiredMixin, ProjectPermissionsMixin, CreateView):
    """A base class for view for creating new project sources."""

    project_permission_required = ProjectPermissionType.EDIT

    def get_initial(self):
        return {
            'project': get_object_or_404(Project, pk=self.kwargs['pk'])
        }

    def form_valid(self, form):
        """Override to set the project for the `Source` and redirect back to that project."""
        pk = self.kwargs['pk']
        file_source = form.save(commit=False)
        file_source.project = get_object_or_404(Project, pk=pk)
        file_source.save()

        if self.request.GET.get('directory'):
            reverse_path = reverse("project_files_path", args=(pk, self.request.GET['directory']))
        else:
            reverse_path = reverse("project_files", args=(pk,))

        return HttpResponseRedirect(reverse_path)


class FileSourceCreateView(SourceCreateView):
    """A view for creating a new, emtpy local file in the project."""

    model = FileSource
    form_class = RelativeFileSourceForm
    template_name = 'projects/filesource_create.html'

    @property
    def current_directory(self) -> str:
        return self.request.GET.get('directory', '')

    def get_context_data(self, **kwargs):
        return super(FileSourceCreateView, self).get_context_data(current_directory=self.current_directory)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_directory'] = self.current_directory
        return kwargs


class DropboxSourceCreateView(SourceCreateView):
    """A view for creating a Dropbox project source."""

    model = DropboxSource
    template_name = 'projects/dropboxsource_create.html'


class GithubSourceCreateView(SourceCreateView):
    """A view for creating a Github project source."""

    model = GithubSource
    form_class = GithubSourceForm
    template_name = 'projects/githubsource_create.html'


class FileSourceUploadView(LoginRequiredMixin, ProjectPermissionsMixin, DetailView):
    """A view for uploading one or more files into the project."""

    model = Project
    template_name = 'projects/filesource_upload.html'
    project_permission_required = ProjectPermissionType.EDIT

    def get_context_data(self, **kwargs):
        self.perform_project_fetch(self.request.user, self.kwargs['pk'])
        context_data = super().get_context_data(**kwargs)
        context_data['upload_directory'] = self.request.GET.get('directory', '')
        return context_data

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        self.perform_project_fetch(request.user, pk)
        self.test_required_project_permission()

        directory = request.GET.get('directory', '')
        while directory.endswith('/'):
            directory = directory[:-1]

        files = request.FILES.getlist('file')
        for file in files:
            if directory:
                file_path = '{}/{}'.format(directory, file.name)
            else:
                file_path = file.name

            source = FileSource.objects.create(
                project=self.project,
                path=file_path,
                file=file
            )
            source.save()

        return HttpResponse()


class FileSourceOpenView(LoginRequiredMixin, ProjectPermissionsMixin, DetailView):
    project_permission_required = ProjectPermissionType.VIEW

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['file_content'] = self.object.pull()
        return data

    def render(self, request: HttpRequest, editing_context: SourceEditContext,
               extra_context: typing.Optional[dict] = None) -> HttpResponse:
        render_context = {
            'file_path': editing_context.path,
            'file_extension': editing_context.extension,
            'file_content': editing_context.content,
            'file_editable': editing_context.editable,
            'source': editing_context.source,
            'supports_commit_message': editing_context.supports_commit_message
        }
        render_context.update(extra_context or {})
        return render(request, 'projects/source_open.html', self.get_render_context(render_context))

    @staticmethod
    def get_default_commit_message(request: HttpRequest):
        return 'Commit from Stencila Hub User {}'.format(request.user)

    def process_get(self, request: HttpRequest, content_facade: SourceContentFacade) -> HttpResponse:
        return self.render(request, content_facade.get_edit_context(), {
            'default_commit_message': self.get_default_commit_message(request)
        })

    def get(self, request: HttpRequest, project_pk: int, pk: int, path: str) -> HttpResponse:
        content_facade = self.get_content_facade(request, project_pk, pk, path)
        return self.process_get(request, content_facade)

    @staticmethod
    def get_github_repository_path(source, file_path):
        repo_path = utf8_path_join(source.subpath, strip_directory(file_path, source.path))
        return repo_path

    def post(self, request: HttpRequest, project_pk: int, pk: int, path: str) -> HttpResponse:
        self.pre_post_check(request, project_pk)

        content_facade = self.get_content_facade(request, project_pk, pk, path)
        return self.perform_post(request, project_pk, path, content_facade)

    def pre_post_check(self, request: HttpRequest, project_pk: int) -> None:
        self.perform_project_fetch(request.user, project_pk)
        if not self.has_permission(ProjectPermissionType.EDIT):
            raise PermissionDenied

    def perform_post(self, request: HttpRequest, project_pk: int, path: str, content_facade: SourceContentFacade):
        commit_message = request.POST.get('commit_message') or self.get_default_commit_message(request)
        if not content_facade.update_content(request.POST['file_content'], commit_message):
            return self.render(request, content_facade.get_edit_context(), {
                'commit_message': commit_message,
                'default_commit_message': self.get_default_commit_message(request)
            })
        messages.success(request, 'Content of {} updated.'.format(os.path.basename(path)))
        directory = os.path.dirname(path)
        if directory:
            reverse_name = 'project_files_path'
            args = (project_pk, directory,)  # type: ignore
        else:
            reverse_name = 'project_files'
            args = (project_pk,)  # type: ignore
        return redirect(reverse(reverse_name, args=args))

    def get_content_facade(self, request, project_pk, pk, path):
        source = self.get_source(request.user, project_pk, pk)
        authentication = LinkedSourceAuthentication(user_github_token(request.user))
        return SourceContentFacade(source, authentication, request, path)


class DiskFileSourceOpenView(FileSourceOpenView):
    project_permission_required = ProjectPermissionType.VIEW

    def get_content_facade(self, request: HttpRequest, project_pk: int, pk: int, path: str):
        fs_path = get_filesystem_project_path(settings.STENCILA_PROJECT_STORAGE_DIRECTORY,
                                              self.get_project(request.user, project_pk), path)
        return SourceContentFacade(DiskFileSource(), None, request, fs_path)

    def get(self, request: HttpRequest, project_pk: int, path: str) -> HttpResponse:  # type: ignore
        content_facade = self.get_content_facade(request, project_pk, -1, path)
        return self.process_get(request, content_facade)

    def post(self, request: HttpRequest, project_pk: int, path: str) -> HttpResponse:  # type: ignore
        self.pre_post_check(request, project_pk)

        content_facade = self.get_content_facade(request, project_pk, -1, path)

        return self.perform_post(request, project_pk, path, content_facade)


class FileSourceUpdateView(LoginRequiredMixin, ProjectPermissionsMixin, UpdateView):
    model = Source
    form_class = SourceUpdateForm
    template_name = 'projects/source_update.html'
    project_permission_required = ProjectPermissionType.EDIT

    def get_success_url(self) -> str:
        path = self.request.GET.get('from')

        if path:
            return reverse('project_files_path', kwargs={'pk': self.kwargs['project_pk'], 'path': path})
        else:
            return reverse('project_files', kwargs={'pk': self.kwargs['project_pk']})

    def get_object(self, *args, **kwargs):
        return self.get_source(self.request.user, self.kwargs['project_pk'], self.kwargs['pk'])


class FileSourceDeleteView(LoginRequiredMixin, ProjectPermissionsMixin, DeleteView):
    model = Source
    template_name = 'confirm_delete.html'
    project_permission_required = ProjectPermissionType.EDIT

    def get_object(self, *args, **kwargs):
        self.perform_project_fetch(self.request.user, self.kwargs['project_pk'])
        source = Source.objects.get(pk=self.kwargs['pk'])

        if source.project != self.project:
            raise PermissionDenied

        return source

    def get_success_url(self) -> str:
        path = self.request.GET.get('from')

        if path:
            return reverse('project_files_path', kwargs={'pk': self.kwargs['project_pk'], 'path': path})
        else:
            return reverse('project_files', kwargs={'pk': self.kwargs['project_pk']})
