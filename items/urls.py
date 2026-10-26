from django.urls import path

from . import views

app_name = "items"

urlpatterns = [
    path("", views.item_list, name="list"),
    path("new/", views.item_create, name="create"),
    path("<int:pk>/", views.item_detail, name="detail"),
    path("<int:pk>/edit/", views.item_edit, name="edit"),
    path("<int:pk>/delete/", views.item_delete, name="delete"),
    path("<int:pk>/resolve/", views.item_resolve, name="resolve"),
    path("comments/<int:pk>/delete/", views.comment_delete, name="comment_delete"),
]