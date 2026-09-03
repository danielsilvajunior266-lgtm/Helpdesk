from django.urls import path
from apps.accounts import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_customer_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
]
