from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import generics,permissions,viewsets
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse,HttpRequest
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db import IntegrityError
from .models import *
from .serializer import *
from .pagination import CustomPagination

# Create your views here.

class VendorList(generics.ListCreateAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    


class VendorDetails(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorDetailSerializer

    

class ProductList(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        qs = super().get_queryset()
        category_id = self.request.GET.get('category')
        if category_id:
            category = ProductCategory.objects.get(id=category_id)
            qs = qs.filter(category=category)
        return qs




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
#     if request.method == 'POST':
#         try:
#             first_name = request.POST.get('first_name')
#             last_name = request.POST.get('last_name')
#             username = request.POST.get('username')
#             email = request.POST.get('email')
#             phone = request.POST.get('phone')
#             password = request.POST.get('password')
#             hashed_password = make_password(password)

#             user = User.objects.create(
#                 first_name=first_name,
#                 last_name=last_name,
#                 username=username,
#                 email=email,
#                 password=hashed_password
#             )

#             if user:
#                 customer = Customer.objects.create(
#                     user=user,
#                     phone=phone,
#                 )
#                 msg = {
#                     'bool': True,
#                     'user': user.id,
#                     'customer': customer.id,
#                     'msg': 'Thanks for your registration. Now you can login.'
#                 }
#         except IntegrityError as e:
#             if 'username' in str(e):
#                 msg = {
#                     'bool': False,
#                     'msg': "Username already exists!"
#                 }
#             elif 'phone' in str(e):
#                 msg = {
#                     'bool': False,
#                     'msg': "Phone number already exists!"
#                 }
#         else:
#             msg = {
#                 'bool': False,
#                 'msg': 'Oops... Something went wrong!'
#             }
#     else:
#         msg = {
#             'bool': False,
#             'msg': 'Invalid request method!'
#         }

#     return JsonResponse(msg)




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




class OrderList(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def post(self,request,*args, **kwargs):
        print(request.POST)
        return super().post(request,*args, **kwargs)
    


class OrderDetails(generics.ListAPIView):
    # queryset = Order.objects.all()
    serializer_class = OrderItemSerializer  

    def get_queryset(self):
        order_id = self.kwargs['pk']
        order = Order.objects.get(id=order_id)
        order_items = OrderItems.objects.filter(order=order)
        return order_items



class OerderItemList(generics.ListCreateAPIView):
    queryset = OrderItems.objects.all()
    serializer_class = OrderItemSerializer



class OrderItemDetailS(generics.RetrieveUpdateDestroyAPIView):
    queryset = OrderItems.objects.all()
    serializer_class = OrderItemSerializer



class CustomerAddressViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerAddressSerializer
    queryset = CustomerAddress.objects.all()



class ProductRatingViewSet(viewsets.ModelViewSet):
    serializer_class = ProiductReviewSerializer
    queryset = ProductRating.objects.all()





################### product Category ###################

class CategoryList(generics.ListCreateAPIView):
    queryset = ProductCategory.objects.all()
    serializer_class = CategorySerializer


class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductCategory.objects.all()
    serializer_class = CategoryDetailSerializer