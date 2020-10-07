from django.contrib import admin
from django.urls import path, include
from django.contrib.flatpages import views as flat_views
from django.conf.urls import handler404, handler500
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken import views

handler404 = 'posts.views.page_not_found'
handler500 = 'posts.views.server_error'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('about-us/', flat_views.flatpage, {'url': '/about-author/'}, name='about'),
    path('terms/', flat_views.flatpage, {'url': '/terms/'}, name='terms'),
    path('about-author/', flat_views.flatpage, {'url': '/about-author/'}, name='about-author'),
    path('about-spec/', flat_views.flatpage, {'url': '/about-spec/'}, name='about-spec'),
    path('', include('posts.urls')),
]

urlpatterns += [
    path('api-token-auth/', views.obtain_auth_token)
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += (path("__debug__/", include(debug_toolbar.urls)),)
