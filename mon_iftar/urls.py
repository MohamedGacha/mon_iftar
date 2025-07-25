# In your main urls.py
from django.contrib import admin
from django.urls import include, path
from .views import health_check 

urlpatterns = [
    path('admin/', admin.site.urls),
    # Routes for user_management app
    path('api/user_management/', include('user_management.urls')),
    # Routes for authentication app
    path('api/authentication/', include('authentication.urls')),
    # Routes for distribution_management app
    path('api/distribution_management/', include('distribution_management.urls')),
    
    # Health check route
    path('health/', health_check), 
]
