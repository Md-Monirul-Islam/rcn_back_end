from django.urls import path
from .import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register('customer-address',views.CustomerAddressViewSet)
router.register('product-rating',views.ProductRatingViewSet)

urlpatterns = [
    path('vendors/',views.VendorList.as_view(),name='vendor_list'),

    path('vendors/<int:pk>/',views.VendorDetails.as_view(),name='vendor_details'),

    path('product-list/',views.ProductList.as_view(),name='product-list'),
    
    path('product-detail/<int:pk>/',views.ProductDetail.as_view(),name='product_detail'),

    path('customers/',views.CustomerList.as_view(),name='customers_list'),

    path('customer/<int:pk>/',views.CustomerDetails.as_view(),name='customer_details'),

    path('orders/',views.OrderList.as_view(),name='order_list'),

    path('order/<int:pk>/',views.OrderDetails.as_view(),name='order_details'),

    path('order-items/',views.OrderList.as_view(),name='order_items_list'),

    path('order-item/<int:pk>/',views.OrderDetails.as_view(),name='order_item'),

]
urlpatterns += router.urls