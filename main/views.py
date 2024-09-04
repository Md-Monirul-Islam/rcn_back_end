from uuid import uuid4
from django.db.models import DateField
from django.shortcuts import redirect, render
import requests
from rest_framework.response import Response
from rest_framework import generics,permissions,viewsets
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseNotAllowed, JsonResponse,HttpRequest
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User,Group
from django.db import IntegrityError
from .models import *
from .serializer import *
from .pagination import CustomPagination
from rest_framework import status
from django.contrib.auth import logout
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotAuthenticated
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from django.db.models import OuterRef, Subquery
from rest_framework.views import APIView
from django.db.models import Q

# Create your views here.

class VendorList(generics.ListCreateAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if 'fetch_limit' in self.request.GET:
            limit = self.request.GET['fetch_limit']
            qs = qs.annotate(downloads=Count('product')).order_by('-downloads','-id')
            qs = qs[:int(limit)]
        return qs
    
    


class VendorDetails(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorDetailSerializer



class VendorProductsView(generics.ListAPIView):
    serializer_class = ProductListSerializer

    def get_queryset(self):
        vendor_id = self.kwargs['vendor_id']
        qs = Product.objects.filter(vendor_id=vendor_id)
        return qs



@csrf_exempt
def vendor_register(request):
    first_name = request.POST.get('first_name')
    last_name = request.POST.get('last_name')
    username = request.POST.get('username')
    email = request.POST.get('email')
    phone = request.POST.get('phone')
    address = request.POST.get('address')
    password = request.POST.get('password')
    hashed_password = make_password(password)
    try:
        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=hashed_password
        )
               
        if user:
            try:
                #Create vendor
                vendor = Vendor.objects.create(
                    user=user,
                    phone=phone,
                    address=address,
                )
                msg = {
                'bool': True,
                'user': user.id,
                'vendor': vendor.id,
                'msg':'Thanks for your registration. Now you can login.'
                }
            except IntegrityError:
                msg = {
                'bool':False,
                'msg':"Phone already exist !!"
            }
        
        else:
            msg = {
                'bool':False,
                'msg':'Oops... Somethings went Wrong !!'
            }
    except IntegrityError:
        msg = {
            'bool':False,
            'msg':"Username already exist !!"
        }
    return JsonResponse(msg)



@csrf_exempt
def vendor_login(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(username=username,password=password)
    if user:
        vendor = Vendor.objects.get(user=user)
        msg = {
        'bool': True,
        'user': user.username,
        'id': vendor.id
        }
    else:
        msg = {
            'bool':False,
            'msg':'Invalid username or password !!'
        }
    return JsonResponse(msg)



@csrf_exempt
def vendor_change_password(request,vendor_id):
    password = request.POST.get('password')
    vendor = Vendor.objects.get(id=vendor_id)
    user = vendor.user
    user.password = make_password(password)
    user.save()
    msg = {'bool':True,'msg':'Password has been changed'}
    return JsonResponse(msg)

    

class ProductList(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by('-downloads','-id')
    serializer_class = ProductListSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        qs = super().get_queryset()
        category_id = self.request.GET.get('category')
        if category_id:
            category = ProductCategory.objects.get(id=category_id)
            qs = qs.filter(category=category)
        
        if 'fetch_limit' in self.request.GET:
            limit = self.request.GET['fetch_limit']
            qs = qs[:int(limit)]

        if 'popular_fetch_limit' in self.request.GET:
            limit = self.request.GET['popular_fetch_limit']
            qs = qs.order_by('-downloads','-id')
            qs = qs[:int(limit)]
        return qs
    


# class ProductList(generics.ListCreateAPIView):
#     queryset = Product.objects.all().order_by('-id')
#     serializer_class = ProductListSerializer
#     pagination_class = CustomPagination
#     permission_classes = [IsAuthenticated]
#     def get_queryset(self):
#         qs = super().get_queryset()
#         user = self.request.user
        
#         if user.is_anonymous:
#             raise NotAuthenticated("User is not authenticated")

#         # Get the Vendor instance related to the user
#         vendor = get_object_or_404(Vendor, user=user)
        
#         category_id = self.request.GET.get('category')
#         if category_id:
#             category = ProductCategory.objects.get(id=category_id)
#             qs = qs.filter(category=category)
        
#         # Filter products by the logged-in vendor
#         qs = qs.filter(vendor=vendor)

#         if 'fetch_limit' in self.request.GET:
#             limit = self.request.GET['fetch_limit']
#             qs = qs[:int(limit)]
#         return qs



class ProductImgsList(generics.ListCreateAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer



class ProductImgsDetail(generics.ListCreateAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        product_id = self.kwargs['product_id']
        qs = qs.filter(product__id=product_id)
        return qs
    


class DeleteProductImgDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer

    



class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer




class TagProductList(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        qs = super().get_queryset()
        tag = self.kwargs['tag']
        qs = qs.filter(tags__icontains=tag)
        return qs
    

@csrf_exempt
def CustomerLogin(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(username=username,password=password)
    if user:
        customer = Customer.objects.get(user=user)
        msg = {
        'bool': True,
        'user': user.username,
        'id': customer.id
        }
    else:
        msg = {
            'bool':False,
            'msg':'Invalid username or password !!'
        }
    return JsonResponse(msg)



@csrf_exempt
def customer_change_password(request,customer_id):
    password = request.POST.get('password')
    customer = Customer.objects.get(id=customer_id)
    user = customer.user
    user.password = make_password(password)
    user.save()
    msg = {'bool':True,'msg':'Password has been changed'}
    return JsonResponse(msg)





@csrf_exempt
def CustomerRegister(request):
    first_name = request.POST.get('first_name')
    last_name = request.POST.get('last_name')
    username = request.POST.get('username')
    email = request.POST.get('email')
    phone = request.POST.get('phone')
    password = request.POST.get('password')
    hashed_password = make_password(password)
    try:
        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=hashed_password
        )
               
        if user:
            try:
                #Create customer
                customer = Customer.objects.create(
                    user=user,
                    phone=phone,
                )
                msg = {
                'bool': True,
                'user': user.id,
                'customer': customer.id,
                'msg':'Thanks for your registration. Now you can login.'
                }
            except IntegrityError:
                msg = {
                'bool':False,
                'msg':"Phone already exist !!"
            }
        
        else:
            msg = {
                'bool':False,
                'msg':'Oops... Somethings went Wrong !!'
            }
    except IntegrityError:
        msg = {
            'bool':False,
            'msg':"Username already exist !!"
        }
    return JsonResponse(msg)


# @csrf_exempt
# def CustomerRegister(request):
#     first_name = request.POST.get('first_name')
#     last_name = request.POST.get('last_name')
#     username = request.POST.get('username')
#     email = request.POST.get('email')
#     phone = request.POST.get('phone')
#     password = request.POST.get('password')
#     hashed_password = make_password(password)

#     try:
#         user = User.objects.create(
#             first_name=first_name,
#             last_name=last_name,
#             username=username,
#             email=email,
#             password=hashed_password
#         )
        
#         if user:
#             try:
#                 # Create customer
#                 customer = Customer.objects.create(
#                     user=user,
#                     phone=phone,
#                 )

#                 # Assign user to the Customer_Permission group
#                 customer_group, created = Group.objects.get_or_create(name='Customer_Permission')
#                 user.groups.add(customer_group)

#                 msg = {
#                     'bool': True,
#                     'user': user.id,
#                     'customer': customer.id,
#                     'msg': 'Thanks for your registration. Now you can login.'
#                 }
#             except IntegrityError:
#                 msg = {
#                     'bool': False,
#                     'msg': "Phone already exists!"
#                 }
#         else:
#             msg = {
#                 'bool': False,
#                 'msg': 'Oops... Something went wrong!'
#             }
#     except IntegrityError:
#         msg = {
#             'bool': False,
#             'msg': "Username already exists!"
#         }

#     return JsonResponse(msg)


# Logout
@api_view(['POST'])
def logout_view(request):
    # # For token-based authentication
    # if request.auth:
    #     request.auth.delete()
    # For session-based authentication
    logout(request)
    return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)





class RelatedProductList(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        product_id = self.kwargs['pk']
        product = Product.objects.get(id=product_id)
        qs = qs.filter(category=product.category).exclude(id=product_id)
        return qs


# class RelatedProductList(generics.ListAPIView):
#     serializer_class = ProductListSerializer

#     def get_queryset(self):
#         product_id = self.kwargs['pk']
#         product = Product.objects.get(id=product_id)
#         related_products = Product.objects.filter(category=product.category).exclude(id=product_id)
#         return related_products

#     def list(self, request, *args, **kwargs):
#         queryset = self.get_queryset()
#         serializer = self.get_serializer(queryset, many=True)
#         data = serializer.data
#         for product in data:
#             product_id = product['id']
#             product['product_image'] = [image.image.url for image in Product.objects.get(id=product_id).product_image.all()]
#         return Response(data)

# class RelatedProductList(generics.ListAPIView):
#     serializer_class = ProductListSerializer

#     def get_queryset(self):
#         product_id = self.kwargs['pk']
#         product = Product.objects.get(id=product_id)
#         related_products = Product.objects.filter(category=product.category).exclude(id=product_id)
#         return related_products

#     def list(self, request, *args, **kwargs):
#         queryset = self.get_queryset()
#         serializer = self.get_serializer(queryset, many=True)
#         data = serializer.data
#         for product in data:
#             product_id = product['id']
#             # Check if product_image exists and is not empty
#             if 'product_image' in product and product['product_image']:
#                 product['product_image'] = [image.image.url for image in Product.objects.get(id=product_id).product_image.all()]
#             else:
#                 # Set a default value for product_image
#                 product['product_image'] = []  # Or set it to a placeholder image URL
#         return Response(data)




class CustomerList(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    


class CustomerDetails(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class UserDetails(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer




class OrderList(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def post(self,request,*args, **kwargs):
        print(request.POST)
        return super().post(request,*args, **kwargs)
    

#### Order Items

class OrderItemsList(generics.ListCreateAPIView):
    queryset = OrderItems.objects.all()
    serializer_class = OrderItemSerializer

    


class OrderDetails(generics.ListAPIView):
    # queryset = Order.objects.all()
    serializer_class = OrderItemSerializer  

    def get_queryset(self):
        order_id = self.kwargs['pk']
        order = Order.objects.get(id=order_id)
        order_items = OrderItems.objects.filter(order=order)
        return order_items



#Customer order item list
class CustomerOrderItemsList(generics.ListAPIView):
    queryset = OrderItems.objects.all()
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        customer_id = self.kwargs['pk']
        qs = qs.filter(order__customer__id=customer_id)
        return qs


#Vendor order item list
class VendorOrderItemsList(generics.ListAPIView):
    queryset = OrderItems.objects.all()
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        vendor_id = self.kwargs['pk']
        qs = qs.filter(product__vendor__id=vendor_id)
        return qs
    


#Vendor customer list
# class VendorCustomerList(generics.ListAPIView):
#     queryset = OrderItems.objects.all()
#     serializer_class = OrderItemSerializer

#     def get_queryset(self):
#         qs = super().get_queryset()
#         vendor_id = self.kwargs['pk']
#         qs = qs.filter(product__vendor__id=vendor_id)
#         return qs


class VendorCustomerList(generics.ListAPIView):
    serializer_class = CustomerSerializer

    def get_queryset(self):
        vendor_id = self.kwargs['pk']
        
        # Subquery to get distinct customer IDs
        subquery = OrderItems.objects.filter(product__vendor__id=vendor_id,order__customer=OuterRef('pk')).values('order__customer').distinct()

        # Get unique customers related to the vendor's products
        customers = Customer.objects.filter(id__in=Subquery(subquery)).distinct()
        
        return customers


    


class VendorCustomerOrderItemList(generics.ListAPIView):
    queryset = OrderItems.objects.all()
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        vendor_id = self.kwargs['vendor_id']
        customer_id = self.kwargs['customer_id']
        qs = qs.filter(product__vendor__id=vendor_id,order__customer__id=customer_id)
        return qs


# class VendorCustomerOrderItemList(generics.ListAPIView):
#     serializer_class = OrderItemSerializer

#     def get_queryset(self):
#         vendor_id = self.kwargs['vendor_id']
#         customer_id = self.kwargs.get('customer_id')  # Use get() to handle missing customer_id

#         if customer_id:
#             queryset = OrderItems.objects.filter(
#                 product__vendor__id=vendor_id,
#                 order__customer__id=customer_id
#             )
#         else:
#             queryset = OrderItems.objects.none()  # Or raise a custom exception

#         return queryset
    


class OrderItemDetailS(generics.RetrieveUpdateDestroyAPIView):
    queryset = OrderItems.objects.all()
    serializer_class = OrderItemSerializer



#Order update
class OrderModify(generics.RetrieveUpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer



#order delete
@csrf_exempt
def delete_customer_orders(request, customer_id):
    if request.method in ["DELETE", "GET"]:
        # Delete orders for the specified customer
        orders = Order.objects.filter(customer__id=customer_id).delete()
        msg = {'bool': bool(orders[0])}  # orders[0] gives the count of deleted objects
        return JsonResponse(msg)
    
    else:
        # Respond with 405 Method Not Allowed for other request methods
        return HttpResponseNotAllowed(['DELETE', 'GET'])



class CustomerAddressViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerAddressSerializer
    queryset = CustomerAddress.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        customer_id = data.get('customer')
        
        if not customer_id:
            return Response({'error': 'Customer ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Invalid Customer ID'}, status=status.HTTP_400_BAD_REQUEST)
        
        data['customer'] = customer.id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    

# customer address list

class CustomerAddressList(generics.ListAPIView):
    queryset = CustomerAddress.objects.all()
    serializer_class = CustomerAddressSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        customer_id = self.kwargs['pk']
        qs = qs.filter(customer__id = customer_id)
        return qs
    


@csrf_exempt
def make_default_address(request, pk):
    if request.method == 'POST':
        address_id = request.POST.get('default_address')
        if address_id:
            # Reset all addresses to not be default
            CustomerAddress.objects.filter(customer=pk).update(default_address=False)
            # Set the selected address as default
            response = CustomerAddress.objects.filter(id=address_id).update(default_address=True)
            msg = {'bool': bool(response)}
            return JsonResponse(msg)
    return JsonResponse({'bool': False})



def customer_dashboard(request, pk):
    customer_id = pk
    # print(customer_id)
    totalAddress = CustomerAddress.objects.filter(customer__id=customer_id).count()
    totalOrder = Order.objects.filter(customer__id=customer_id).count()
    totalWishList = WishList.objects.filter(customer__id=customer_id).count()
    
    context = {
        'totalOrder': totalOrder,
        'totalWishList': totalWishList,
        'totalAddress': totalAddress,
    }
    return JsonResponse(context)



#Vendor dashboard
def vendor_dashboard(request, pk):
    vendor_id = pk
    # print(vendor_id)
    totalProducts = Product.objects.filter(vendor__id=vendor_id).count()
    totalOrders = OrderItems.objects.filter(product__vendor__id=vendor_id).count()
    # totalCustomers = OrderItems.objects.filter(product__vendor__id=vendor_id).values('order__customer').count()
    totalCustomers = OrderItems.objects.filter(product__vendor__id=vendor_id).values('order__customer').distinct().count()
    
    context = {
        'totalOrders': totalOrders,
        'totalCustomers': totalCustomers,
        'totalProducts': totalProducts,
    }
    return JsonResponse(context)



#Vendor daily reports
#only for date wise
# class VendorDailyReport(generics.ListAPIView):
#     serializer_class = VendorDailyReportSerializer
#     # queryset = OrderItems.objects.all()

#     def get_queryset(self):
#         # qs = super().get_queryset()
#         vendor_id = self.kwargs['pk']
#         # Adjusting the annotation to use 'total_orders' instead of 'id__count'
#         qs = OrderItems.objects.filter(product__vendor__id=vendor_id).values('order__order_time__date').annotate(total_orders=Count('id'))
#         return qs
    


#date,month and year wise
class VendorDailyReport(generics.ListAPIView):
    serializer_class = VendorDailyReportSerializer

    def get_queryset(self):
        vendor_id = self.kwargs['pk']
        time_frame = self.request.query_params.get('time_frame', 'daily')

        if time_frame == 'monthly':
            qs = OrderItems.objects.filter(product__vendor__id=vendor_id).annotate(
                month=TruncMonth('order__order_time')
            ).values(
                month=TruncMonth('order__order_time', output_field=DateField())
            ).annotate(total_orders=Count('id')).order_by('month')
        elif time_frame == 'yearly':
            qs = OrderItems.objects.filter(product__vendor__id=vendor_id).annotate(
                year=TruncYear('order__order_time')
            ).values(
                year=TruncYear('order__order_time', output_field=DateField())
            ).annotate(total_orders=Count('id')).order_by('year')
        else:  # Default to daily
            qs = OrderItems.objects.filter(product__vendor__id=vendor_id).annotate(
                date=TruncDate('order__order_time')
            ).values(
                date=TruncDate('order__order_time', output_field=DateField())
            ).annotate(total_orders=Count('id')).order_by('date')
        
        return qs



        


#Vendor daily reports /// this code properly work without @property in model of OrderItems
# class VendorDailyReport(generics.ListAPIView):
#     serializer_class = VendorDailyReportSerializer
#     # queryset = OrderItems.objects.all()

#     def get_queryset(self):
#         # qs = super().get_queryset()
#         vendor_id = self.kwargs['pk']
#         # Adjusting the annotation to use 'total_orders' instead of 'id__count'
#         qs = OrderItems.objects.filter(product__vendor__id=vendor_id).values('order__order_time__date').annotate(total_orders=Count('id'))
#         return qs


class ProductRatingViewSet(viewsets.ModelViewSet):
    serializer_class = ProductReviewSerializer
    queryset = ProductRating.objects.all()





################### product Category ###################

class CategoryList(generics.ListCreateAPIView):
    queryset = ProductCategory.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if 'category_fetch_limit' in self.request.GET:
            limit = self.request.GET['category_fetch_limit']
            qs = qs.annotate(downloads=Count('category_product'))
            qs = qs[:int(limit)]
        return qs


class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductCategory.objects.all()
    serializer_class = CategoryDetailSerializer




@csrf_exempt
def Update_Order_Status(request, pk):
    order_id = pk
    if request.method == "POST":
        update_order_status = Order.objects.filter(id=order_id).update(order_status=True)
        msg = {
            'bool': False,
        }
        if update_order_status:
            msg = {
                'bool': True,
            }
        return JsonResponse(msg)
    


@csrf_exempt
def Update_Product_Download_Count(request, product_id):
    if request.method == "POST":
        product = Product.objects.get(id=product_id)
        totalDownloads = product.downloads
        totalDownloads += 1
        if totalDownloads == 0:
            totalDownloads = 1
        update_product_download_Count = Product.objects.filter(id=product_id).update(downloads=totalDownloads)
        msg = {
            'bool': False,
        }
        if update_product_download_Count:
            msg = {
                'bool': True,
            }
        return JsonResponse(msg)
    



### WishList
class Wish_List(generics.ListCreateAPIView):
    queryset = WishList.objects.all()
    serializer_class = WishListSerializer



@csrf_exempt
def check_in_wishlist(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        product_id = request.POST.get('product')
        if WishList.objects.filter(customer_id=customer_id, product_id=product_id).exists():
            return JsonResponse({'bool': True})
        else:
            return JsonResponse({'bool': False})
    return JsonResponse({'error': 'Invalid request method'}, status=405)



class Wish_Items(generics.ListAPIView):
    queryset = WishList.objects.all()
    serializer_class = WishListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        customer_id = self.kwargs['pk']
        qs = qs.filter(customer_id=customer_id)
        return qs



@csrf_exempt
def remove_from_wishlist(request):
    if request.method == 'POST':
        wishlist_id = request.POST.get('wishlist_id')
        response = WishList.objects.filter(id=wishlist_id).delete()
        msg = {'bool': False}
        if response[0]:
            msg = {'bool': True}
    return JsonResponse(msg)




class VendorCategoryProductsView(generics.ListAPIView):
    def get(self, request, seller_id, category_title, *args, **kwargs):
        # Filter products by seller and category
        products = Product.objects.filter(vendor__id=seller_id, category__title=category_title)

        # Serialize the data
        serializer = ProductListSerializer(products, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    



#search view
# class ProductSearchView(APIView):
#     def get(self, request, format=None):
#         query = request.GET.get('q', '')
#         if query:
#             products = Product.objects.filter(
#                 Q(title__icontains=query) |
#                 Q(category__title__icontains=query) |
#                 Q(vendor__user__username__icontains=query)
#             )
#             serializer = ProductSerializer(products, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             return Response({"error": "No search query provided."}, status=status.HTTP_400_BAD_REQUEST)

class ProductSearchView(APIView):
    def get(self, request, format=None):
        query = request.GET.get('q', '')
        if query:
            products = Product.objects.filter(
                Q(title__icontains=query) |
                Q(category__title__icontains=query) |
                Q(vendor__user__username__icontains=query)
            )
            serializer = ProductSerializer(products, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "No search query provided."}, status=status.HTTP_400_BAD_REQUEST)



# Payment using Sslcommerz

base_url = 'http://127.0.0.1:8000'

@api_view(['POST'])
def initiate_payment(request):
    if request.method == 'POST':
        post_data = request.data
        order_id = post_data.get('order_id')
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order does not exist"}, status=400)
        
        total_amount = post_data.get('amount')
        customer = order.customer
        user = customer.user
        
        # Fetch the default customer address
        customer_address = customer.customer_address.filter(default_address=True).first()
        
        if not customer_address:
            return Response({"error": "Default customer address does not exist"}, status=400)
        
        # Set transaction ID and create a new transaction
        transaction_id = uuid4().hex
        transaction = Transaction.objects.create(
            transaction_id=transaction_id,
            amount=total_amount,
            user=user,
            customer_address=customer_address,
            customer_email=user.email,
            customer_phone=customer.phone,
            customer_postcode=customer_address.post,
        )
        
        # Prepare payment data using the customer's default address
        payment_data = {
            'store_id': 'kopot665596f0af929',
            'store_passwd': 'kopot665596f0af929@ssl',
            'total_amount': transaction.amount,
            'currency': transaction.currency,
            'tran_id': transaction.transaction_id,
            'product_name': 'Order Items',
            'product_category': 'Various',
            'product_profile': 'General',
            'success_url': f'{base_url}/api/success/',
            'fail_url': f'{base_url}/api/fail/',
            'cancel_url': f'{base_url}/api/cancel/',
            'shipping_method': 'Courier',
            'cus_country': 'Bangladesh',
            'cus_name': user.get_full_name(),
            'cus_email': transaction.customer_email,
            'cus_phone': transaction.customer_phone,
            'cus_add1': customer_address.address,
            'cus_city': customer_address.city,
            'cus_postcode': transaction.customer_postcode,
            'ship_name': user.get_full_name(),
            'ship_add1': customer_address.address,
            'ship_city': customer_address.city,
            'ship_state': customer_address.city,
            'ship_postcode': customer_address.post,
            'ship_country': 'Bangladesh',
        }

        response = requests.post('https://sandbox.sslcommerz.com/gwprocess/v4/api.php', data=payment_data)
        return Response(response.json())
    



@api_view(['POST'])
def payment_success(request):
    if request.method == 'POST':
        post_data = request.POST
        transaction_id = post_data.get('tran_id')
        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
            transaction.status = 'SUCCESS'
            transaction.save()
            client_site_url = f'http://localhost:5173/'
            return redirect(client_site_url)
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)
            

@api_view(['POST'])
def payment_fail(request):
    if request.method == 'POST':
        post_data = request.POST
        transaction_id = post_data.get('tran_id')
        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
            transaction.status = 'FAILED'
            transaction.save()
            client_site_url = f'http://localhost:5173/paymentFail?transaction_id={transaction_id}&status={transaction.status}'
            return redirect(client_site_url)
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def payment_cancel(request):
    if request.method == 'POST':
        post_data = request.POST
        transaction_id = post_data.get('tran_id')
        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
            transaction.status = 'CANCELLED'
            transaction.save()
            return Response({'status': 'cancelled'})
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)