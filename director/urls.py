from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path

from users.views import (
    UserSettingsView,
    UserSignupView,
    UserSigninView,
    UserSignoutView,
    BetaTokenView)

from checkouts.views import (
    CheckoutListView,
    CheckoutCreateView,
    CheckoutReadView,
    CheckoutOpenView,
    CheckoutSaveView,
    CheckoutCloseView)

from projects.views import (
    ProjectListView,
    ProjectCreateView,
    ProjectUpdateView,
    ProjectDeleteView,
    ProjectArchiveView,

    ProjectHostManifestView,
    ProjectHostSessionsView)

from views import HomeView

urlpatterns = [
    # Project CRUD
    path('projects/', include([
        # Generic views
        path('', ProjectListView.as_view(), name='project_list'),
        path('create/', ProjectCreateView.as_view(), name='project_create'),
        path('<int:pk>/update/', ProjectUpdateView.as_view(), name='project_update'),
        #path('update/save-general', ProjectGeneralSaveView.as_view(), name='project_general_save'),
        #path('update/save-session-parameters', ProjectSessionParametersSaveView.as_view(),
        #     name='project_session_parameters_save'),
        #path('update/save-access', ProjectAccessSaveView.as_view(), name='project_access_save'),
        path('<int:pk>/delete/', ProjectDeleteView.as_view(), name='project_delete'),
        path('<int:pk>/archive/', ProjectArchiveView.as_view(), name='project_archive'),
        #path('<int:pk>/sessions/', ProjectSessionsListView.as_view(), name='project_sessions'),
        # Per project Host API
        path('<str:token>/host/', include([
            path('v0/', include([
                path('manifest', ProjectHostManifestView.as_view(), {'version': 0}),
                re_path(r'^environ/(?P<environ>.*)', ProjectHostSessionsView.as_view())
            ])),
            path('v1/', include([
                path('manifest', ProjectHostManifestView.as_view(), {'version': 1}),
                re_path(r'^sessions/(?P<environ>.*)', ProjectHostSessionsView.as_view())
            ]))
        ])),
        # Type-specific views
        #path('files/<int:pk>/', FilesSourceReadView.as_view(), name='filesproject_read'),
        #path('files/<int:pk>/update/', FilesSourceUpdateView.as_view(), name='filesproject_update'),
        #path('files/<int:pk>/upload/', FilesSourceUploadView.as_view(), name='filesproject_upload'),
        #path('files/<int:pk>/remove/<int:file>/', FilesProjectRemoveView.as_view(), name='filesproject_remove'),
    ])),

    # Checkout CRUD
    path('checkouts/', include([
        path('', CheckoutListView.as_view(), name='checkout_list'),
        path('create/', CheckoutCreateView.as_view(), name='checkout_create'),
        path('<int:pk>/', CheckoutReadView.as_view(), name='checkout_read'),
        path('<int:pk>/open/', CheckoutOpenView.as_view(), name='checkout_open'),
        path('<int:pk>/save/', CheckoutSaveView.as_view(), name='checkout_save'),
        path('<int:pk>/close/', CheckoutCloseView.as_view(), name='checkout_close')
    ])),
    # Shortcut to `checkout_create`
    path('open/', CheckoutCreateView.as_view(), name='checkout_create_shortcut'),

    # User sign in, settings etc
    path('beta/', BetaTokenView.as_view(), name='user_beta'),
    path('me/', UserSettingsView.as_view(), name='user_settings'),
    path('me/signup/', UserSignupView.as_view(), name='user_signup'),
    path('me/signin/', UserSigninView.as_view(), name='user_signin'),
    path('me/signout/', UserSignoutView.as_view(), name='user_signout'),
    path('me/', include('allauth.urls')),

    # Staff admin
    path('admin/', admin.site.urls),

    # Home page
    path('', HomeView.as_view(), name='home'),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path('debug/', include(debug_toolbar.urls)),
                  ] + urlpatterns
