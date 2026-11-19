from django.urls import path

from . import views

app_name = "news"

urlpatterns = [
    path("", views.home, name="home"),
    path("news/", views.news_list, name="list"),
    path("news/new/", views.news_create, name="create"),
    path("news/<int:news_id>/", views.news_detail, name="detail"),
    path("action-error/", views.action_error, name="error"),
    path("notifications/", views.notifications, name="notifications"),
    path("notifications/<int:notification_id>/read/", views.notification_read, name="notification_read"),
]
