from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('financas.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # ← ESSA LINHA ADICIONA /accounts/login/
]
