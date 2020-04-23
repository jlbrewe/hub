from django.urls import path, include

from general.api.routers import OptionalSlashRouter
from jobs.api.views import JobsViewSet, AccountsJobsViewSet, AccountsZonesViewSet

jobs = OptionalSlashRouter()
jobs.register("jobs", JobsViewSet, "api-jobs")

accounts_jobs = OptionalSlashRouter()
accounts_jobs.register("jobs", AccountsJobsViewSet, "api-accounts-jobs")

accounts_zones = OptionalSlashRouter()
accounts_zones.register("zones", AccountsZonesViewSet, "api-accounts-zones")

urlpatterns = jobs.urls + [
    path("accounts/<int:pk>/", include(accounts_jobs.urls)),
    path("accounts/<int:pk>/", include(accounts_zones.urls)),
]
