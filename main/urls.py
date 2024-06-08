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

    ######## Customer section ########
    path('customers/',views.CustomerList.as_view(),name='customers_list'),

    path('customer/<int:pk>/',views.CustomerDetails.as_view(),name='customer_details'),

    path('user/<int:pk>/',views.UserDetails.as_view(),name='user_details'),

    path('customer-login/',views.CustomerLogin,name='customer_login'),

    path('customer-register/',views.CustomerRegister,name='customer_register'),

    path('orders/',views.OrderList.as_view(),name='order_list'),

    path('order/<int:pk>/',views.OrderDetails.as_view(),name='order_details'),

    path('order-items/',views.OrderItemsList.as_view(),name='order_items'),

    path('customer/<int:pk>/order-items/',views.CustomerOrderItemsList.as_view(),name='customer_order_items'),

    path('update-order-status/<int:pk>/',views.Update_Order_Status, name='update_order_status'),

    path('update-product-download-count/<str:product_id>/', views.Update_Product_Download_Count, name='update_product_download_count'),

    #WishList
    path('wishlist/', views.Wish_List.as_view(),name='wishlist'),

    path('check-in-wishlist/',views.check_in_wishlist,name='check_in_wishlist'),

    path('customer/<int:pk>/wishitems/',views.Wish_Items.as_view(),name='wishitems'),

    path('remove-from-wishlist/', views.remove_from_wishlist, name='remove_from_wishlist'),

]
urlpatterns += router.urls