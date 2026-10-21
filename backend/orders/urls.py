from django.urls import path

from . import views

urlpatterns = [
    path('orders/', views.create_order, name='order-create'),
    path('orders/<str:public_id>/', views.retrieve_order, name='order-detail'),
    path('orders/<str:public_id>/notification/', views.update_notification, name='order-notification'),
    path('staff/login/', views.staff_login, name='staff-login'),
    path('staff/orders/', views.staff_orders, name='staff-orders'),
    path('staff/orders/<str:public_id>/status/', views.update_order_status, name='staff-order-status'),
]
