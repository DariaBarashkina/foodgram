from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import get_object_or_404, redirect
from django.urls import include, path

from recipes.models import Recipe


def redirect_to_recipe(request, code):
    recipe = get_object_or_404(Recipe, short_code=code)
    return redirect(f'/recipes/{recipe.id}')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<str:code>/', redirect_to_recipe, name='short-link'),
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
