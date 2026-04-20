from django.shortcuts import get_object_or_404
from django.http import HttpResponsePermanentRedirect

from .models import Recipe


def redirect_to_recipe(request, code):
    recipe = get_object_or_404(Recipe, short_code=code)

    url = request.build_absolute_uri(f'/recipes/{recipe.id}')
    return HttpResponsePermanentRedirect(url)
