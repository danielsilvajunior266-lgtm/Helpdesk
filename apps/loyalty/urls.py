from django.urls import path
from apps.loyalty import views

urlpatterns = [
    path('', views.loyalty_dashboard, name='dashboard'),
    path('configure/', views.loyalty_configure, name='configure'),
    path('accounts/<int:account_id>/redeem/', views.redeem_reward, name='redeem'),
]
