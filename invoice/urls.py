from django.urls import path
from .views import index, generate

urlpatterns = [
    path("", index, name="index"),
    path("generate/", generate, name="generate"),
    
]
