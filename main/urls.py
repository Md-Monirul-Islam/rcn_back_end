from django.urls import path
from .import views
from rest_framework import routers
from .views import CustomerAddressViewSet, ProductSearchView

router = routers.DefaultRouter()
router.register(r'address', CustomerAddressViewSet, basename='address')
router.register('product-rating',views.ProductRatingViewSet)

urlpatterns = [
    ############ Vendors ##########
    path('vendors/',views.VendorList.as_view(),name='vendor_list'),

    path('vendors/<int:pk>/',views.VendorDetails.as_view(),name='vendor_details'),

    path('vendor-register/',views.vendor_register,name='vendor_register'),

    path('vendor-login/',views.vendor_login,name='vendor_login'),

    path('vendor/<int:pk>/order-items/',views.VendorOrderItemsList.as_view(),name='vendor_order_items'),

    path('vendor/<int:pk>/customers/',views.VendorCustomerList.as_view(),name='vendor_customer_list'),

    path('vendor/<int:vendor_id>/customer/<int:customer_id>/order-items/',views.VendorCustomerOrderItemList.as_view(),name="vendor's_customer_order_list"),

    path('vendor/<int:pk>/dashboard/',views.vendor_dashboard,name='vendor_dashboard'),

    path('vendor/<int:pk>/seller-daily-report/',views.VendorDailyReport.as_view(),name='seller_daily_report'),

    path("vendor-change-password/<int:vendor_id>/",views.vendor_change_password, name="vendor_change_password"),

    path('vendor/<int:vendor_id>/products/', views.VendorProductsView.as_view(), name='vendor-products'),

    path('vendor-products/',views.VendorProductList.as_view(),name='vendor-product-list'),

    ######## Product ########
    path('products/',views.ProductList.as_view(),name='product-list'),

    path('products/<str:tag>',views.TagProductList.as_view(),name='tag_product_list'),
    
    path('product/<int:pk>/',views.ProductDetail.as_view(),name='product_detail'),

    path('related-products/<int:pk>/',views.RelatedProductList.as_view(),name='related_product'),

    path('product-imgs/',views.ProductImgsList.as_view(),name='product_image_list'),

    path('product-imgs/<int:product_id>/',views.ProductImgsDetail.as_view(),name='product_imgs'),

    path('product-img-delete/<int:pk>/',views.DeleteProductImgDetail.as_view(),name='product_imgs_delete'),

    path('order-modify/<int:pk>/',views.OrderModify.as_view(),name='order_modify'),

    path('delete-customer-orders/<int:customer_id>/',views.delete_customer_orders,name='order_delete'),

    ######## Product Category ########
    path('categories/',views.CategoryList.as_view(),name='categories'),

    path('add-category/',views.AddCategory.as_view(),name='categories'),
    
    path('category/<int:pk>/',views.CategoryDetail.as_view(),name='category_detail'),

    ######## Customer section ########
    path('customers/',views.CustomerList.as_view(),name='customers_list'),

    path('customer/<int:pk>/',views.CustomerDetails.as_view(),name='customer_details'),
    
    path('customer/<int:pk>/address-list/',views.CustomerAddressList.as_view(),name='customer_address_list'),

    path('make-default-address/<int:pk>/',views.make_default_address,name='make_default_address'),

    path('check-default-address/', views.check_default_address, name='check-default-address'),

    path('user/<int:pk>/',views.UserDetails.as_view(),name='user_details'),

    path('customer-login/',views.CustomerLogin,name='customer_login'),

    path('customer-logout/',views.logout_view,name='customer_logout'),

    path('customer-register/',views.CustomerRegister,name='customer_register'),

    path('orders/',views.OrderList.as_view(),name='order_list'),

    path('submit-order/', views.SubmitOrder.as_view(), name='submit-order'),

    path('order/<int:pk>/',views.OrderDetails.as_view(),name='order_details'),

    path('order-items/',views.OrderItemsList.as_view(),name='order_items'),

    path('customer/<int:pk>/order-items/',views.CustomerOrderItemsList.as_view(),name='customer_order_items'),

    # path('address',views.CustomerAddressViewSet.as_view(),name='address'),

    path('update-order-status/<int:pk>/',views.Update_Order_Status, name='update_order_status'),

    path('update-product-download-count/<str:product_id>/', views.Update_Product_Download_Count, name='update_product_download_count'),

    #WishList
    path('wishlist/', views.Wish_List.as_view(),name='wishlist'),

    path('check-in-wishlist/',views.check_in_wishlist,name='check_in_wishlist'),

    path('customer/<int:pk>/wishitems/',views.Wish_Items.as_view(),name='wishitems'),

    path('remove-from-wishlist/', views.remove_from_wishlist, name='remove_from_wishlist'),

    path('customer-dashboard/<int:pk>/',views.customer_dashboard,name='customer_dashboard'),

    path("customer-change-password/<int:customer_id>/",views.customer_change_password, name="customer_change_password"),

    path('sellers/<int:seller_id>/categories/<str:category_title>/products/', views.VendorCategoryProductsView.as_view(), name='seller_category_products'),

    path('search/', ProductSearchView.as_view(), name='product-search'),

    path('initiate-payment/', views.initiate_payment, name='initiate-payment'),
    path('payment-success/', views.payment_success, name='payment-success'),
    path('payment-fail/', views.payment_fail, name='payment-fail'),
    path('payment-cancel/', views.payment_cancel, name='payment-cancel'),


    path('admin-dashboard/',views.admin_dashboard,name='admin_dashboard'),
    path('superuser-login/', views.SuperuserLoginView.as_view(), name='superuser-login'),
    path('delete-vendor/<int:pk>/', views.delete_vendor, name='delete_vendor'),
    path('orders-show-for-admin/',views.OrderListForAdminView.as_view(),name='order_list'),
    path('customer/<int:customer_id>/order-items/',views.CustomerOrderItemListShowForAdmin.as_view(),name="customer_order_item_show_for_admin"),
    path('vendor/<int:vendor_id>/ordered-products/', views.VendorOrderedProductsListView.as_view(), name='vendor_ordered_products_list'),
    path('orders-search-by-date/', views.search_orders_by_date, name='search_orders_by_date'),
    path('vendor/<int:vendor_id>/search-orders/', views.VendorDateWiseOrderSearch.as_view(), name='vendor-datewise-orders'),
    path('search-orders/<int:vendor_id/', views.VendorOrderSearchView.as_view(), name='search_orders_by_id'),

]
urlpatterns += router.urls