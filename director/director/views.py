import hashlib
import io
import os
import re
from django.http import Http404, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.contrib.auth.models import User
from django.views.generic import View, TemplateView, ListView, DetailView, CreateView, \
     FormView
from django.views import static
from django.urls import reverse
from uuid import uuid4

import allauth.account.views
from .auth import login_guest_user
from .forms import UserSignupForm, UserSigninForm, StencilaProjectRenameForm, \
     StencilaProjectUploadForm, BetaTokenForm
from .storer import Storer
from .models import Project, StencilaProject, Cluster, ClusterError

class SigninRequiredMixin(AccessMixin):
    # Not required until we bring back guests

    def get_login_url(self):
        if self.request.user.is_authenticated and self.request.user.email == 'guest':
            return 'user_join'
        return 'user_signin'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.email == 'guest':
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

BETA_TOKENS = ['abc123']

class BetaTokenRequiredMixin(AccessMixin):

    def get_login_url(self):
        return 'beta-token'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.GET.get('token', '') in BETA_TOKENS:
            request.session['beta_token'] = request.GET['token']
        if not request.session.get('beta_token', '') in BETA_TOKENS:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

class Error404View(TemplateView):
    template_name = 'error404.html'


class Error500View(TemplateView):
    template_name = 'error500.html'


class BetaTokenView(FormView):
    template_name = 'beta_token.html'
    form_class = BetaTokenForm

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid() and form.cleaned_data['token'] in BETA_TOKENS:
            request.session['beta_token'] = form.cleaned_data['token']
            url = request.GET.get('next', reverse('user_signin'))
            return redirect(url)
        else:
            form.add_error("token", "Incorrect token")
        return self.render_to_response(dict(form=form))

class UserSignupView(BetaTokenRequiredMixin, allauth.account.views.SignupView):

    template_name = "user/signup.html"
    form_class = UserSignupForm


class UserSigninView(BetaTokenRequiredMixin, allauth.account.views.LoginView):

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


class UserSettingsView(LoginRequiredMixin, TemplateView):

    template_name = "user/settings.html"


class OpenAddress(LoginRequiredMixin, TemplateView):
    template_name = 'open-address.html'

    def get(self, request, address):
        try:
            storer = Storer.get_instance_by_address(address)
        except:
            raise Http404

        project, _ = Project.objects.get_or_create(address=address)
        project.users.add(request.user)

        project_session_id = (request.session.session_key + address).encode('utf-8')
        project_session_id = hashlib.sha1(project_session_id).hexdigest()
        if not 'convert' in request.session:
            request.session['convert'] = {}
        request.session['convert'][project_session_id] = project.id

        try:
            cluster = Cluster.choose(user=request.user, project=project)
        except ClusterError as e:
            cluster = None

        return self.render_to_response(dict(
            address=address,
            cluster=cluster,
            project_session_id=project_session_id,
        ))

    def post(self, request, address):
        # Address is a storer code, and the address components are in post variables
        try:
            storer = Storer.get_instance_by_provider(address)
        except:
            raise Http404
        form = storer.get_open_form(request.POST)
        if form.is_valid():
            return redirect('open', address=form.get_address())
        raise Http404

class ConvertView(View):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(dict(status=404, error="Not found"))
        if not "project_session_id" in kwargs:
            return JsonResponse(dict(status=404, error="Not found"))
        project_session_id = kwargs.get("project_session_id")
        if not project_session_id in request.session.get('convert', {}):
            return JsonResponse(dict(status=404, error="Not found"))
        return super().dispatch(request, *args, **kwargs)

class ConvertStart(ConvertView):

    def get(self, request, project_session_id):
        project_id = request.session['convert'][project_session_id]
        storer = Storer.get_instance_by_project_id(project_id)
        storer.ui_convert(project_session_id)
        return JsonResponse(dict(status=200, message="Conversion finished"))

class OpenProgress(ConvertView):

    def get(self, request, project_session_id):
        rel_path = os.path.join(project_session_id, 'log.json')
        full_path = os.path.join(settings.CONVERT_WORKDIR, rel_path)
        if not os.path.exists(full_path):
            return JsonResponse(dict(status=404, error="Not found"))
        return static.serve(request, rel_path, document_root=settings.CONVERT_WORKDIR)

class GalleryView(ListView):
    template_name = 'gallery.html'
    model = Project

    def get_queryset(self):
        return Project.objects.filter(gallery=True)[:12]

class ProjectListView(LoginRequiredMixin, ListView):
    template_name = 'project_list.html'
    model = Project

    def get_queryset(self):
        return self.request.user.projects.all()

    def get_context_data(self, *args, **kwargs):
        context = super(ProjectListView, self).get_context_data(*args, **kwargs)
        accounts = {a.provider: a for a in self.request.user.socialaccount_set.all()}
        enabled = []
        disabled = []
        providers = ['github']
        for provider in providers:
            account = accounts.get(provider, None)
            if account:
                enabled.append(Storer.get_instance_by_account(account))
            else:
                disabled.append(Storer.get_instance_by_provider(provider))
        context['storers'] = dict(enabled=enabled, disabled=disabled)
        return context

    def post(self, request, **kwargs):
        project_id = request.POST.get("project", 0)
        project = get_object_or_404(Project, id=project_id)
        if hasattr(project, 'stencilaproject') \
          and project.stencilaproject.owner == request.user:
          project.stencilaproject.delete()
        else:
            project.users.remove(request.user)
        return redirect('list-projects')

class StorerProjectBlock(LoginRequiredMixin, TemplateView):
    template_name = 'storer_unit_list.html'

    def get_context_data(self):
        return dict(storer=self.storer, units=self.storer.units())

    def get(self, request, **kwargs):
        try:
            self.account = self.request.user.socialaccount_set.get(provider=kwargs['storer'])
            self.storer = Storer.get_instance_by_account(account=self.account)
        except Exception:
            raise Http404

        return self.render_to_response(self.get_context_data())

class BrowseFolder(LoginRequiredMixin, TemplateView):
    template_name = 'storer_browse_folder.html'

    def get(self, request, address):
        try:
            storer = Storer.get_instance_by_address(address)
        except:
            raise Http404
        context = self.get_context_data()
        context['storer'] = storer.code
        context['address'] = address
        return self.render_to_response(context)

    def post(self, request, address):
        # Address is a storer code, and the address components are in post variables
        try:
            storer = Storer.get_instance_by_provider(address)
        except:
            raise Http404
        form = storer.get_browse_form(request.POST)
        if not form.is_valid():
            raise Http404
        context = self.get_context_data()
        context.update(form.cleaned_data)
        context['storer'] = storer.code
        context['address'] = form.get_address()
        return self.render_to_response(context)

class StorerRefsBlock(LoginRequiredMixin, TemplateView):
    template_name = 'storer_refs_block.html'

    def get_context_data(self):
        return dict(
            address=self.address, storer=self.storer, refs=self.storer.refs())

    def get(self, request, **kwargs):
        self.address = kwargs['address']
        self.storer = Storer.get_instance_by_address(self.address)
        self.storer.account = request.user.socialaccount_set.get(provider=self.storer.code)
        return self.render_to_response(self.get_context_data())

class StorerFolderBlock(LoginRequiredMixin, TemplateView):
    template_name = 'storer_folder_block.html'

    def get_context_data(self):
        return dict(
            address=self.address, storer=self.storer, files=self.storer.folder_contents())

    def get(self, request, **kwargs):
        self.address = kwargs['address']
        self.storer = Storer.get_instance_by_address(self.address)
        self.storer.account = request.user.socialaccount_set.get(provider=self.storer.code)
        return self.render_to_response(self.get_context_data())

class StencilaProjectFileView(LoginRequiredMixin, DetailView):
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

class StencilaProjectFilesBlock(LoginRequiredMixin, DetailView):
    model = StencilaProject
    template_name = 'project_filelist_block.html'

    def get(self, request, **kwargs):
        self.object = get_object_or_404(
            StencilaProject, owner__username=kwargs['user'], name=kwargs['project'])
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

class StencilaProjectDetailView(LoginRequiredMixin, DetailView):
    model = StencilaProject
    template_name = 'project_files.html'

    def get_object_or_404(self, **kwargs):
        return get_object_or_404(
            StencilaProject, owner__username=kwargs['user'], name=kwargs['project'])

    def get(self, request, **kwargs):
        self.object = self.get_object_or_404(**kwargs)
        context = self.get_context_data(object=self.object)
        if self.object.owner == request.user:
            context['rename_form'] = StencilaProjectRenameForm(instance=self.object)
            context['upload_form'] = StencilaProjectUploadForm(instance=self.object)
        return self.render_to_response(context)

    def post(self, request, **kwargs):
        self.object = self.get_object_or_404(**kwargs)

        if self.object.owner != request.user:
            raise Http404

        context = self.get_context_data(object=self.object)

        if 'rename' in request.POST:
            rename_form = StencilaProjectRenameForm(request.POST, instance=self.object)
            if rename_form.is_valid():
                rename_form.save()
                return redirect(
                    'project-files', user=request.user.username,
                    project=self.object.name)
            context['rename_form'] = rename_form

        if 'upload' in request.POST:
            upload_form = StencilaProjectUploadForm(request.POST, instance=self.object)
            files = self.request.FILES.getlist('upload')
            if upload_form.is_valid():
                self.object.upload(files)
                self.object.project.users.add(request.user)
                return redirect(
                    'project-files', user=request.user.username,
                    project=self.object.name)
            context['upload_form'] = upload_form

        elif 'delete' in request.POST:
            filename = request.POST['delete']
            self.object.delete_file(filename)

        if not 'upload_form' in context:
            context['upload_form'] = StencilaProjectUploadForm(instance=self.object)
        if not 'rename_form' in context:
            context['rename_form'] = StencilaProjectRenameForm(instance=self.object)

        return self.render_to_response(context)

class CreateStencilaProjectView(LoginRequiredMixin, View):

    def create_project(self):
        return StencilaProject.get_or_create_for_user(
            self.request.user, uuid=uuid4())

    def post(self, request, *args, **kwargs):
        stencila_project = self.create_project()
        return redirect(
            'project-files', user=request.user.username, project=stencila_project.name)

class OpenNew(CreateStencilaProjectView):

    def post(self, request, *args, **kwargs):
        stencila_project = self.create_project()
        return redirect('open', address=stencila_project.project.address)
