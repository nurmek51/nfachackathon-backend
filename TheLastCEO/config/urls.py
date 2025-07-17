"""
URL configuration for TheLastCEO project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from game import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

api_urlpatterns = [
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', views.profile, name='profile'),
    path('games/available/', views.available_games, name='available_games'),
    path('games/create/', views.create_game, name='create_game'),
    path('games/<uuid:session_id>/join/', views.join_game, name='join_game'),
    path('avatar/options/', views.avatar_options, name='avatar_options'),
    path('avatar/customize/', views.customize_avatar, name='customize_avatar'),
    path('quiz/questions/', views.quiz_questions, name='quiz_questions'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
] + api_urlpatterns
