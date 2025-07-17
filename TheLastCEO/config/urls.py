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
api_urlpatterns = [
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('games/available/', views.available_games, name='available_games'),
    path('games/&lt;uuid:session_id&gt;/join/', views.join_game, name='join_game'),
    path('stats/', views.game_statistics, name='game_statistics'),
    path('hall-of-fame/', views.hall_of_fame, name='hall_of_fame'),
    path('shop/items/', views.available_items, name='available_items'),
    path('shop/purchase/', views.purchase_item, name='purchase_item'),
]
urlpatterns = [
    path('admin/', admin.site.urls),
] + api_urlpatterns
