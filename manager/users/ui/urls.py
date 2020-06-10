from django.urls import include, path

from users.ui.views import (
    SigninView,
    SignoutView,
    SignupView,
    UsernameView,
)

urlpatterns = [
    path("signup/", SignupView.as_view(), name="ui-users-signup"),
    path("signin/", SigninView.as_view(), name="ui-users-signin"),
    path("signout/", SignoutView.as_view(), name="ui-users-signout"),
    path("username/change/", UsernameView.as_view(), name="ui-users-username"),
    path("", include("allauth.urls")),
]
