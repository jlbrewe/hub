import re
from django.http import Http404, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.views.generic import View, TemplateView, ListView, DetailView, CreateView
import allauth.account.views
import io
import uuid
from .auth import login_guest_user
from .forms import UserSignupForm, UserSigninForm, CreateProjectForm
from .storer import storers
from .models import Project, StencilaProject, Cluster

class FrontPageView(TemplateView):
    template_name = 'index.html'


class UserSignupView(allauth.account.views.SignupView):

    template_name = "user/signup.html"
    form_class = UserSignupForm


class UserSigninView(allauth.account.views.LoginView):

    template_name = "user/signin.html"
    form_class = UserSigninForm


class UserSignoutView(allauth.account.views.LogoutView):

    template_name = "user/signout.html"


class UserJoinView(View):

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.email == 'guest':
            logout(request)
            return redirect('/me/signup/')
        else:
            return redirect('/')


class UserSettingsView(TemplateView):

    template_name = "user/settings.html"


class OpenInput(TemplateView):
    template_name = 'open-input.html'


class OpenAddress(TemplateView):
    template_name = 'open-address.html'

    def get(self, request, address=None):
        cluster = None
        token = None
        if address:
            try:
                proto, path = address.split("://")
                storer = storers[proto]
                assert(storer.valid_path(path))
                valid = True
            except:
                valid = False

            if valid:
                if not request.user.is_authenticated:
                    login_guest_user(request)

                cluster, token = Project.open(user=request.user, address=address)
        return self.render_to_response(dict(
            address=address,
            cluster=cluster,
            token=token
        ))


class GalleryView(ListView):
    template_name = 'gallery.html'
    model = Project

    def get_queryset(self):
        return Project.objects.filter(gallery=True)[:12]

class ProjectListView(ListView):
    template_name = 'project_list.html'
    model = Project

    def get_queryset(self):
        return self.request.user.projects.all()

    def get_context_data(self, *args, **kwargs):
        context = super(ProjectListView, self).get_context_data(*args, **kwargs)
        accounts = {}
        for account in self.request.user.socialaccount_set.all():
            accounts[account.provider] = storers[account.provider]().account_info(account)
        context.update(accounts=accounts)
        return context

class StencilaProjectFileView(DetailView):
    model = StencilaProject

    def get(self, request, **kwargs):
        self.object = get_object_or_404(
            StencilaProject, owner__username=kwargs['user'], name=kwargs['project'])
        try:
            filename = kwargs['filename']
        except KeyError:
            raise Http404
        s = io.BytesIO()
        self.object.get_file(filename, s)
        response = HttpResponse(s.getvalue())
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        return response

class StencilaProjectApiDetailView(DetailView):
    model = StencilaProject

    def get(self, request, **kwargs):
        try:
            self.object = StencilaProject.objects.get(
	            owner__username=kwargs['user'], name=kwargs['project'])
            listing = self.object.list_files()
        except Exception:
            return JsonResponse(dict(message="Not found"), status=404)
        return JsonResponse(dict(objects=listing), status=200)

class StencilaProjectDetailView(DetailView):
    model = StencilaProject
    template_name = 'project_files.html'

    def get(self, request, **kwargs):
        self.object = get_object_or_404(
            StencilaProject, owner__username=kwargs['user'], name=kwargs['project'])
        context = self.get_context_data(
            object=self.object, owner=int(request.user == self.object.owner))
        return self.render_to_response(context)

class CreateProjectView(TemplateView):
    template_name = 'project_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('home')
        if request.user.email == 'guest':
            logout(request)
            return redirect('user_signup')
        # TODO Check email address is verified
        return super(CreateProjectView, self).dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        context = dict(form=CreateProjectForm(), uuid=uuid.uuid4())
        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        form = CreateProjectForm(self.request.POST)
        files = self.request.FILES.getlist('file')
        uuid = self.request.POST.get('uuid')
        if form.is_valid():
            stencila_project = StencilaProject.get_or_create_for_user(self.request.user, uuid)
            stencila_project.upload(files)
            stencila_project.project.users.add(self.request.user)
            return redirect(
                'project-files',
                user=self.request.user.username,
                project=stencila_project.name)
        return self.render_to_response(dict(form=form))
