from django.urls import path
from apps.orders import views

urlpatterns = [
    path('', views.kanban_view, name='kanban'),
    path('orders/new/', views.order_create, name='create'),
    path('orders/<int:order_id>/', views.order_detail, name='detail'),
    path('orders/<int:order_id>/status/', views.update_status, name='update_status'),
    path('orders/<int:order_id>/photos/', views.upload_photo, name='upload_photo'),
]
