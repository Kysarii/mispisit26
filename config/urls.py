from django.urls import include, path


urlpatterns = [
    path("", include("news.urls")),
]

handler404 = "news.views.page_not_found"
