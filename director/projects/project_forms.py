import typing

from django import forms

from lib.forms import FormWithSubmit, ModelFormWithSubmit
from .project_models import Project, SessionParameters


class ProjectCreateForm(ModelFormWithSubmit):

    class Meta:
        model = Project
        fields = ['account', 'name', 'description', 'public']
        widgets = {
            'name': forms.TextInput()
        }


class ProjectGeneralForm(ModelFormWithSubmit):

    class Meta:
        model = Project
        fields = ['name', 'description', 'public']
        widgets = {
            'name': forms.TextInput()
        }


class ProjectSettingsMetadataForm(ModelFormWithSubmit):

    class Meta:
        model = Project
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput()
        }


class ProjectSettingsSessionsForm(ModelFormWithSubmit):

    class Meta:
        model = Project
        fields = []

    sessions_total = forms.IntegerField(
        required=False,
        min_value=1,
        help_text='The maximum number of sessions to run at one time. Leave blank for unlimited.'
    )

    sessions_concurrent = forms.IntegerField(
        required=False,
        min_value=1,
        help_text='The total maximum number of sessions allowed to create. Leave blank for unlimited.'
    )

    sessions_queued = forms.IntegerField(
        required=False,
        min_value=1,
        help_text='The total maximum number of sessions allowed to create. Leave blank for unlimited.'
    )

    memory = forms.FloatField(
        min_value=0,
        required=False,
        help_text='Gigabytes (GB) of memory allocated.',
        widget=forms.NumberInput()
    )

    cpu = forms.FloatField(
        label="CPU",
        required=False,
        min_value=1,
        max_value=100,
        help_text='CPU shares (out of 100 per CPU) allocated.',
        widget=forms.NumberInput()
    )

    network = forms.FloatField(
        min_value=0,
        required=False,
        help_text='Gigabytes (GB) of network transfer allocated. Leave blank for unlimited.',
        widget=forms.NumberInput()
    )

    lifetime = forms.IntegerField(
        min_value=0,
        required=False,
        help_text='Minutes before the session is terminated (even if active). Leave blank for unlimited.',
        widget=forms.NumberInput()
    )

    timeout = forms.IntegerField(
        min_value=0,
        required=False,
        help_text='Minutes of inactivity before the session is terminated. Leave blank for unlimited.',
        widget=forms.NumberInput()
    )

    @staticmethod
    def initial(project):
        initial = {}
        initial['sessions_total'] = project.sessions_total
        initial['sessions_concurrent'] = project.sessions_concurrent
        initial['sessions_queued'] = project.sessions_queued
        initial['memory'] = project.session_parameters.memory
        initial['cpu'] = project.session_parameters.cpu
        initial['network'] = project.session_parameters.network
        initial['lifetime'] = project.session_parameters.lifetime
        initial['timeout'] = project.session_parameters.timeout
        return initial

    def clean(self) -> dict:
        cleaned_data = super().clean()

        if cleaned_data['sessions_total'] is not None and \
           cleaned_data['sessions_concurrent'] is not None and \
           cleaned_data['sessions_concurrent'] > cleaned_data['sessions_total']:
            self.add_error('sessions_concurrent',
                           'The maximum number of concurrent Sessions must be less than the maximum total Sessions.')

        if cleaned_data['lifetime'] is not None and (
                cleaned_data['timeout'] is None
                or cleaned_data['timeout'] > cleaned_data['lifetime']):
            self.add_error('timeout', 'The idle timeout must be less that the maximum lifetime of the Session.')

        return cleaned_data

    def save(self, commit=True):
        project = super().save(commit=False)

        project.sessions_total = self.cleaned_data['sessions_total']
        project.sessions_concurrent = self.cleaned_data['sessions_concurrent']
        project.sessions_queued = self.cleaned_data['sessions_queued']
        project.session_parameters.memory = self.cleaned_data['memory']

        if commit:
            project.session_parameters.save()
            project.save()

        return project
