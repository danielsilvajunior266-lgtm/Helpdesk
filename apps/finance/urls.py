from django.urls import path
from apps.finance import views

urlpatterns = [
    path('', views.cash_book, name='cash_book'),
    path('entries/new/', views.entry_create, name='entry_create'),
]
