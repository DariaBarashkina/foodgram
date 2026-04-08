from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.shortcuts import redirect, get_object_or_404
from recipes.models import Recipe


def redirect_to_recipe(request, code):
    recipe = get_object_or_404(Recipe, short_code=code)
    return redirect(f'/recipes/{recipe.id}/')


def redirect_to_edit(request, pk):
    return redirect(f'/recipes/{pk}edit/')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<str:code>/', redirect_to_recipe, name='short-link'),
    re_path(r'^recipes/(?P<pk>\d+)/+/edit/$', redirect_to_edit),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
