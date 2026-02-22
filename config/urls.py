# from django.conf import settings
# from django.conf.urls.static import static
# from django.contrib import admin
# from django.urls import include, path, re_path
# from .scheme import swagger_urlpatterns
# from django.shortcuts import redirect
# from apps.dashboard.users import user_login, user_logout
# import debug_toolbar
# def redirect_dashboard(request):
#     return redirect("dashboard")
#     from drf_spectacular.views import (
#     SpectacularAPIView,
#     SpectacularSwaggerView,
# )


# urlpatterns = [
#     path("api/customer/", include("apps.customer.urls")),
#     path("api/product/", include("apps.product.urls")),
#     path("api/merchant/", include("apps.merchant.urls")),
#     path("admin/", admin.site.urls, name="admin"),
#     path(
#         "dashboard/", include("apps.dashboard.urls"), name="dashboard"
#     ),
#     path("__debug__/", include(debug_toolbar.urls)),
#     path("login/", user_login, name="login_page"),
#     path('logout/', user_logout, name='logout'),
#     path("", redirect_dashboard),
#      # schema (json)
#     path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

#     # swagger UI
#     path("swagger/", SpectacularSwaggerView.as_view(url_name="schema")),

#     # qolgan url lar
#     path("admin/", admin.site.urls),
# ] + swagger_urlpatterns
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve   
from django.shortcuts import redirect

from apps.dashboard.users import user_login, user_logout

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

import debug_toolbar


def redirect_dashboard(request):
    return redirect("dashboard")


urlpatterns = [
    # API lar
    path("api/customer/", include("apps.customer.urls")),
    path("api/product/", include("apps.product.urls")),
    path("api/merchant/", include("apps.merchant.urls")),

    # Admin
    path("admin/", admin.site.urls),

    # Dashboard
    path("dashboard/", include("apps.dashboard.urls")),
    path("", redirect_dashboard),

    # Auth
    path("login/", user_login, name="login_page"),
    path("logout/", user_logout, name="logout"),

    # Debug
    path("__debug__/", include(debug_toolbar.urls)),

    # Swagger / OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema")),
]

# Static & media
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]


