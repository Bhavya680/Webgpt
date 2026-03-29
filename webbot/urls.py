from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from core.views import landing_page
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Root landing page and auth
    path('', landing_page, name='landing'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('signup/', landing_page, name='signup'),

    # API routes
    path('api/', include('core.urls')),
    path('api/token/', obtain_auth_token),
]
