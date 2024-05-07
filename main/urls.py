from django.urls import path
from .import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register('customer-address',views.CustomerAddressViewSet)
router.register('product-rating',views.ProductRatingViewSet)

urlpatterns = [
    ############ Vendors ##########
    path('vendors/',views.VendorList.as_view(),name='vendor_list'),

    path('vendors/<int:pk>/',views.VendorDetails.as_view(),name='vendor_details'),

    ######## Product ########
    path('products/',views.ProductList.as_view(),name='product-list'),

    path('products/<str:tag>',views.TagProductList.as_view(),name='tag_product_list'),
    
    path('product/<int:pk>/',views.ProductDetail.as_view(),name='product_detail'),

    path('related-products/<int:pk>/',views.RelatedProductList.as_view(),name='related_product'),

    ######## Product Category ########
    path('categories/',views.CategoryList.as_view(),name='categories'),
    
    path('category/<int:pk>/',views.CategoryDetail.as_view(),name='category_detail'),

    path('customers/',views.CustomerList.as_view(),name='customers_list'),

    path('customer/<int:pk>/',views.CustomerDetails.as_view(),name='customer_details'),

    path('customer-login/',views.CustomerLogin,name='customer_login'),

    path('orders/',views.OrderList.as_view(),name='order_list'),

    path('order/<int:pk>/',views.OrderDetails.as_view(),name='order_details'),

    path('order-items/',views.OrderList.as_view(),name='order_items_list'),

    path('order-item/<int:pk>/',views.OrderDetails.as_view(),name='order_item'),

]
urlpatterns += router.urls