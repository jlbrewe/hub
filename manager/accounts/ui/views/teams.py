from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from accounts.api.views import AccountsTeamsViewSet, TeamDestroySerializer


@login_required
def list(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    """List teams."""
    viewset = AccountsTeamsViewSet.init("list", request, args, kwargs)
    account, role = viewset.get_account_role()
    teams = viewset.get_queryset(account)
    return render(
        request,
        "accounts/teams/list.html",
        dict(account=account, role=role, teams=teams),
    )


@login_required
def create(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    """Create a team."""
    viewset = AccountsTeamsViewSet.init("create", request, args, kwargs)
    account, role = viewset.get_account_role()
    serializer = viewset.get_serializer()
    return render(
        request,
        "accounts/teams/create.html",
        dict(account=account, role=role, serializer=serializer),
    )


@login_required
def retrieve(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    """Retrieve an account."""
    viewset = AccountsTeamsViewSet.init("retrieve", request, args, kwargs)
    account, role, team = viewset.get_account_role_team()
    return render(
        request,
        "accounts/teams/retrieve.html",
        dict(account=account, role=role, team=team),
    )


@login_required
def update(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    """Update or destroy a team."""
    viewset = AccountsTeamsViewSet.init("partial_update", request, args, kwargs)
    account, role, team = viewset.get_account_role_team()
    update_serializer = viewset.get_serializer(team)
    destroy_serializer = TeamDestroySerializer()
    return render(
        request,
        "accounts/teams/update.html",
        dict(
            account=account,
            role=role,
            team=team,
            update_serializer=update_serializer,
            destroy_serializer=destroy_serializer,
        ),
    )
