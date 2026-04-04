from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from core.views import landing_page, signup_page, login_page

urlpatterns = [
    path('admin/', admin.site.urls),

    # Root landing page and auth
    path('', landing_page, name='landing'),
    path('login/', login_page, name='login'),
    path('signup/', signup_page, name='signup'),

    # API routes
    path('api/', include('core.urls')),
    path('api/token/', obtain_auth_token),
    
    # Dashboard routes
    path('dashboard/', include('dashboard.urls')),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT or settings.STATICFILES_DIRS[0])
