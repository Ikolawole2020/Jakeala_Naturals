from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/admin/", include("admin_api.urls")),
    path("api/", include("accounts.urls")),
    path("api/", include("catalog.urls")),
    path("api/", include("commerce.urls")),
    path("api/", include("content.urls")),
    path("api/", include("payments.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Jakeala Naturals"
admin.site.site_title = "Jakeala Admin"
admin.site.index_title = "Store administration"
