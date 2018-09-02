import typing

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import View, ListView, CreateView, UpdateView, DeleteView

from users.views import BetaTokenRequiredMixin
from .models import Project
from .project_forms import ProjectCreateForm


class ProjectListView(BetaTokenRequiredMixin, ListView):
    template = "projects/project_list.html"

    def get_queryset(self) -> QuerySet:
        """
        Only list those projects that the user is the creator pf
        or, if unauthenticated, all public projects
        """
        if self.request.user.is_authenticated:
            return Project.objects.filter(
                Q(creator=self.request.user) | Q(public=True)
            )
        else:
            return Project.objects.filter(public=True)


class ProjectCreateView(LoginRequiredMixin, CreateView):
    form_class = ProjectCreateForm
    template_name = "projects/project_create.html"

    def form_valid(self, form):
        """
        If the project creation form is valid them make the current user the
        project creator
        """
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """
        Redirect to the project update page when it has bee
        successfully created
        """
        return reverse("project_update", kwargs={'pk': self.object.pk})


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    fields = '__all__'
    template_name = 'projects/project_update.html'


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/project_delete.html'
    success_url = reverse_lazy('project_list')


class ProjectArchiveView(LoginRequiredMixin, View):

    @staticmethod
    def get(request: HttpRequest, pk: typing.Optional[int]) -> HttpResponse:
        project = get_object_or_404(Project, pk=pk)
        if not owner_access_check(request, project, "creator"):
            raise PermissionDenied

        archive = project.pull()
        body = archive.getvalue()

        response = HttpResponse(body, content_type='application/x-zip-compressed')
        response['Content-Disposition'] = 'attachment; filename={}.zip'.format('project.name')
        return response
