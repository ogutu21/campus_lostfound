from django.urls import path

from . import dashboard, views

app_name = "items"

urlpatterns = [
    path("", views.item_list, name="list"),
    path("new/", views.item_create, name="create"),
    path("<int:pk>/", views.item_detail, name="detail"),
    path("<int:pk>/edit/", views.item_edit, name="edit"),
    path("<int:pk>/delete/", views.item_delete, name="delete"),
    path("<int:pk>/resolve/", views.item_resolve, name="resolve"),
    path("<int:pk>/report/", views.report_create, name="report"),
    path("<int:pk>/claim/", views.claim_create, name="claim"),
    path("<int:pk>/contact/", views.thread_start, name="thread_start"),
    path("comments/<int:pk>/delete/", views.comment_delete, name="comment_delete"),
    path("claims/", views.claims_received, name="claims"),
    path("claims/<int:pk>/decide/", views.claim_decide, name="claim_decide"),
    path("messages/", views.inbox, name="inbox"),
    path("messages/<int:pk>/", views.thread_detail, name="thread"),

    # Staff dashboard
    path("dashboard/", dashboard.dashboard, name="dashboard"),
    path("dashboard/reports/<int:pk>/", dashboard.report_resolve, name="report_resolve"),
    path("dashboard/users/<int:pk>/unlock/", dashboard.unlock_user, name="unlock_user"),
]