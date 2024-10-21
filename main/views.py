import json
from uuid import uuid4
from django.db.models import DateField
from django.shortcuts import redirect
import requests
from rest_framework.response import Response
from rest_framework import generics,viewsets
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseNotAllowed, JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db import IntegrityError
from .models import *
from .serializer import *
from .pagination import CustomPagination
from rest_framework import status
from django.contrib.auth import logout
from rest_framework.decorators import api_view,permission_classes
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly,AllowAny,IsAdminUser
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotAuthenticated
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncMonth, TruncYear, TruncDay, TruncWeek
from django.db.models import OuterRef, Subquery
from rest_framework.views import APIView
from django.db.models import Q
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils.dateparse import parse_date
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime
import decimal
from decimal import Decimal, InvalidOperation
import logging
from django.db.models import Sum, F, DecimalField

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
    shop_name = request.POST.get('shop_name')
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
                    shop_name=shop_name,
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
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'bool': False, 'msg': 'Invalid JSON input'})

        username = data.get('username')
        password = data.get('password')

        user = authenticate(username=username, password=password)

        if user:
            try:
                vendor = Vendor.objects.get(user=user)

                # Generate JWT tokens for the authenticated user
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                # Return success message with tokens and vendor info
                msg = {
                    'bool': True,
                    'user': user.username,
                    'id': vendor.id,
                    'access_token': access_token,  # JWT access token
                    'refresh_token': refresh_token,  # JWT refresh token
                }
            except Vendor.DoesNotExist:
                msg = {
                    'bool': False,
                    'msg': 'Vendor not found for this user!'
                }
        else:
            msg = {
                'bool': False,
                'msg': 'Invalid username or password!'
            }

        return JsonResponse(msg)
    else:
        return JsonResponse({'bool': False, 'msg': 'Invalid request method. Only POST is allowed.'})



@csrf_exempt
@permission_classes([IsAuthenticated])
def vendor_change_password(request,vendor_id):
    password = request.POST.get('password')
    vendor = Vendor.objects.get(id=vendor_id)
    user = vendor.user
    user.password = make_password(password)
    user.save()
    msg = {'bool':True,'msg':'Password has been changed'}
    return JsonResponse(msg)

    

# @permission_classes([IsAuthenticatedOrReadOnly])
class ProductList(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by('-downloads','-id')
    serializer_class = ProductListSerializer
    pagination_class = CustomPagination
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]

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
    


class AddCouponView(generics.ListCreateAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponCodeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        vendor = get_object_or_404(Vendor, user=user)
        product_id = self.request.data.get('products')  # Expect a single product ID

        # Check if the product belongs to the vendor
        if product_id:
            product = get_object_or_404(Product, id=product_id, vendor=vendor)
            coupon = serializer.save(vendor=vendor, product=product)  # Save coupon
            return Response(CouponCodeSerializer(coupon).data, status=status.HTTP_201_CREATED)  # Return the created coupon data
        else:
            return Response({"detail": "Product must be specified."}, status=status.HTTP_400_BAD_REQUEST)
        



class CouponDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponCodeSerializer
    # permission_classes = [IsAuthenticated]
    


@api_view(['GET'])
def apply_coupon(request):
    product_id = request.query_params.get('product_id')
    coupon_code = request.query_params.get('coupon_code')

    try:
        product = Product.objects.get(id=product_id)
        final_price = product.get_final_price(coupon_code)
        
        return Response({
            'discount_applied': product.price - final_price,  # Discount amount
            'discount_price': final_price  # Final price after discount
        })
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)
    

# @permission_classes([IsAuthenticatedOrReadOnly])
class VendorProductList(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by('-id')
    serializer_class = ProductListSerializer
    pagination_class = CustomPagination
    authentication_classes = [JWTAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        if user.is_anonymous:
            raise NotAuthenticated("User is not authenticated")

        # Get the Vendor instance related to the user
        vendor = get_object_or_404(Vendor, user=user)
        
        category_id = self.request.GET.get('category')
        if category_id:
            category = ProductCategory.objects.get(id=category_id)
            qs = qs.filter(category=category)
        
        # Filter products by the logged-in vendor
        qs = qs.filter(vendor=vendor)

        if 'fetch_limit' in self.request.GET:
             limit = self.request.GET['fetch_limit']
             qs = qs[:int(limit)]

        if 'popular_fetch_limit' in self.request.GET:
            limit = self.request.GET['popular_fetch_limit']
            qs = qs.order_by('-downloads','-id')
            qs = qs[:int(limit)]
        return qs



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
    



@permission_classes([IsAuthenticated])
class ProductSpecificationView(APIView):
    def post(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        specifications = request.data.get('specifications', [])

        # Check if product_id is provided
        if not product_id:
            return Response({"error": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the product by ID
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product with the given ID does not exist."}, status=status.HTTP_404_NOT_FOUND)

        # Loop through the specifications and create ProductSpecification entries
        for spec in specifications:
            for feature in spec.get('features', []):
                ProductSpecification.objects.create(
                    product=product,
                    title=spec.get('title'),
                    feature_name=feature.get('feature_name'),
                    feature_value=feature.get('feature_value'),
                )

        return Response({"message": "Specifications added successfully."}, status=status.HTTP_201_CREATED)
    



# class VendorIncomeView(APIView):
#     permission_classes = [AllowAny]

#     def get(self, request, vendor_id):
#         # Daily income
#         daily_income = (
#             OrderItems.objects.filter(order__vendor_id=vendor_id)
#             .annotate(day=TruncDay('order__order_time'))
#             .values('day')
#             .annotate(total=Sum(F('price') * F('quantity'), output_field=DecimalField()))
#             .order_by('day')
#         )

#         # Weekly income
#         weekly_income = (
#             OrderItems.objects.filter(order__vendor_id=vendor_id)
#             .annotate(week=TruncWeek('order__order_time'))
#             .values('week')
#             .annotate(total=Sum(F('price') * F('quantity'), output_field=DecimalField()))
#             .order_by('week')
#         )

#         # Monthly income
#         monthly_income = (
#             OrderItems.objects.filter(order__vendor_id=vendor_id)
#             .annotate(month=TruncMonth('order__order_time'))
#             .values('month')
#             .annotate(total=Sum(F('price') * F('quantity'), output_field=DecimalField()))
#             .order_by('month')
#         )

#         # Yearly income
#         yearly_income = (
#             OrderItems.objects.filter(order__vendor_id=vendor_id)
#             .annotate(year=TruncYear('order__order_time'))
#             .values('year')
#             .annotate(total=Sum(F('price') * F('quantity'), output_field=DecimalField()))
#             .order_by('year')
#         )

#         # Grand total income
#         grand_total = (
#             OrderItems.objects.filter(order__vendor_id=vendor_id)
#             .aggregate(total=Sum(F('price') * F('quantity'), output_field=DecimalField()))['total'] or 0
#         )

#         # Prepare response data
#         data = {
#             "daily_income": list(daily_income),
#             "weekly_income": list(weekly_income),
#             "monthly_income": list(monthly_income),
#             "yearly_income": list(yearly_income),
#             "grand_total": grand_total,
#         }

#         return Response(data)


class VendorIncomeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, vendor_id):
        # Exclude cancelled orders
        non_cancelled_orders = OrderItems.objects.filter(
            order__vendor_id=vendor_id, 
            order__order_status__in=['Confirm', 'Shipped', 'Delivered']
        )

        # Daily income
        daily_income = (
            non_cancelled_orders
            .annotate(day=TruncDay('order__order_time'))
            .values('day')
            .annotate(total=Sum(F('price') * F('quantity'), output_field=DecimalField()))
            .order_by('day')
        )

        # Weekly income
        weekly_income = (
            non_cancelled_orders
            .annotate(week=TruncWeek('order__order_time'))
            .values('week')
            .annotate(total=Sum(F('price') * F('quantity'), output_field=DecimalField()))
            .order_by('week')
        )

        # Monthly income
        monthly_income = (
            non_cancelled_orders
            .annotate(month=TruncMonth('order__order_time'))
            .values('month')
            .annotate(total=Sum(F('price') * F('quantity'), output_field=DecimalField()))
            .order_by('month')
        )

        # Yearly income
        yearly_income = (
            non_cancelled_orders
            .annotate(year=TruncYear('order__order_time'))
            .values('year')
            .annotate(total=Sum(F('price') * F('quantity'), output_field=DecimalField()))
            .order_by('year')
        )

        # Grand total income (excluding cancelled orders)
        grand_total = (
            non_cancelled_orders
            .aggregate(total=Sum(F('price') * F('quantity'), output_field=DecimalField()))['total'] or 0
        )

        # Prepare response data
        data = {
            "daily_income": list(daily_income),
            "weekly_income": list(weekly_income),
            "monthly_income": list(monthly_income),
            "yearly_income": list(yearly_income),
            "grand_total": grand_total,
        }

        return Response(data)
    



class ProductSpecificationListView(generics.ListAPIView):
    serializer_class = ProductSpecificationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        product_id = self.kwargs['product_id']
        return ProductSpecification.objects.filter(product_id=product_id)
    



class DeleteProductImgDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer

    


@permission_classes([IsAuthenticatedOrReadOnly])
class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all().order_by('-id')
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
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'bool': False, 'msg': 'Invalid Username or Password'})

        username = data.get('username')
        password = data.get('password')

        user = authenticate(username=username, password=password)

        if user:
            try:
                customer = Customer.objects.get(user=user)

                # Generate JWT tokens for the authenticated user
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                # Return success message with tokens and customer info
                msg = {
                    'bool': True,
                    'user': user.username,
                    'id': customer.id,
                    'access_token': access_token,  # JWT access token
                    'refresh_token': refresh_token,  # JWT refresh token
                }
            except Customer.DoesNotExist:
                msg = {
                    'bool': False,
                    'msg': 'Customer not found for this user!'
                }
        else:
            msg = {
                'bool': False,
                'msg': 'Invalid username or password!'
            }

        return JsonResponse(msg)
    else:
        return JsonResponse({'bool': False, 'msg': 'Invalid request method. Only POST is allowed.'})



@csrf_exempt
@permission_classes([IsAuthenticated])
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




# Logout
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        # Blacklist the refresh token for JWT
        refresh_token = request.data.get("refresh_token")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logout(request)
            
            return Response({"message": "Logged out successfully and token blacklisted"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Refresh token not provided"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)





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
    permission_classes = [IsAuthenticated, IsAdminUser]
    


class CustomerDetails(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]


class UserDetails(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer




class OrderList(generics.ListAPIView):
    queryset = Order.objects.all().order_by('-id')
    serializer_class = OrderSerializer
    authentication_classes = [JWTAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request,*args, **kwargs):
        print(request.POST)
        return super().post(request,*args, **kwargs)
    



# class SubmitOrder(APIView):
    # permission_classes = [IsAuthenticated]

    # def post(self, request, *args, **kwargs):
    #     customer = request.user.customer
    #     cart_data = request.data.get('cart_items', [])
    #     total_amount = request.data['total_amount']
    #     payment_method = request.data.get('payment_method', 'Online Payment')
    #     select_courier = request.data.get('select_courier', None)
    #     coupon_code = request.data.get('coupon_code', None)

    #     total_amount = decimal.Decimal(total_amount)

    #     # Validate the courier selection
    #     if not select_courier:
    #         return Response({'error': 'Please select a courier service.'}, status=status.HTTP_400_BAD_REQUEST)

    #     # Calculate the total amount on the backend
    #     first_vendor = None
    #     product_list = []
    #     for item in cart_data:
    #         product_id = item.get('product_id')
    #         quantity = item.get('quantity', 1)
    #         product = get_object_or_404(Product, id=product_id)

    #         # Set the vendor to the first product's vendor
    #         if not first_vendor:
    #             first_vendor = product.vendor

    #         total_amount += product.price * quantity
    #         product_list.append({
    #             'title': product.title,
    #             'price': product.price,
    #             'image': product.image.url
    #         })

    #     # Validate the coupon code if provided
    #     discount_amount = 0
    #     if coupon_code:
    #         coupon = get_object_or_404(Coupon, code=coupon_code, is_active=True)
    #         discount_amount = coupon.discount_amount
    #         total_amount -= discount_amount  # Apply discount

    #     # Set order status based on payment method
    #     order_status = 'Confirm' if payment_method == 'mobile-banking' else 'Pending'

    #     # Create the Order and associate it with the first vendor
    #     order = Order.objects.create(
    #         customer=customer,
    #         vendor=first_vendor,
    #         total_amount=total_amount,
    #         order_status=order_status,
    #         payment_method=payment_method,
    #         select_courier=select_courier
    #     )

    #     # Create OrderItems for each product in the cart
    #     for item in cart_data:
    #         product_id = item.get('product_id')
    #         quantity = item.get('quantity', 1)
    #         product = get_object_or_404(Product, id=product_id)

    #         OrderItems.objects.create(
    #             order=order,
    #             product=product,
    #             quantity=quantity,
    #             price=product.price
    #         )

    #     # Send confirmation email
    #     customer_email = customer.user.email
    #     vendor = first_vendor.user  # Get the associated vendor user
    #     vendor_first_name = vendor.first_name
    #     vendor_last_name = vendor.last_name
    #     vendor_email = vendor.email
    #     vendor_phone = first_vendor.phone
    #     vendor_shop_name = first_vendor.shop_name

    #     # Email subject
    #     subject = 'Thank You for Your Purchase! Order Confirmation'

    #     # Render email body using a template
    #     context = {
    #         'customer_name': customer.user.first_name,
    #         'order_number': order.id,
    #         'order_date': order.order_time,
    #         'product_list': product_list,
    #         'vendor_first_name': vendor_first_name,
    #         'vendor_last_name': vendor_last_name,
    #         'vendor_email': vendor_email,
    #         'vendor_phone': vendor_phone,
    #         'payment_method': payment_method,
    #         'select_courier': select_courier,
    #         'vendor_shop_name': vendor_shop_name,
    #         'discount_amount': discount_amount  # Include the discount in the email
    #     }

    #     # Prepare the email message
    #     html_message = render_to_string('order_confirmation_email.html', context)
    #     plain_message = strip_tags(html_message)

    #     recipient_list = [customer_email]
    #     send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, recipient_list, html_message=html_message)

    #     # Save the sent email details in the SentEmail model
    #     SentEmail.objects.create(
    #         recipient=customer_email,
    #         subject=subject,
    #         message=plain_message,
    #         customer=customer.user,  # Link the customer
    #         vendor=vendor  # Link the vendor's user
    #     )

    #     # Serialize and return the response
        # order_serializer = OrderSerializer(order)
        # return Response(order_serializer.data, status=status.HTTP_201_CREATED)
    

logger = logging.getLogger(__name__)

class SubmitOrder(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        customer = request.user.customer
        cart_data = request.data.get('cart_items', [])
        payment_method = request.data.get('payment_method', 'Online Payment')
        select_courier = request.data.get('select_courier', None)
        coupon_code = request.data.get('coupon_code', None)
        discount_price = request.data.get('discount_price') 

        # Initialize total_amount as a Decimal
        total_amount = Decimal(0)  # Start from 0
        logger.info(f'Initialized total_amount: {total_amount}')

        # Ensure courier is selected
        if not select_courier:
            return Response({'error': 'Please select a courier service.'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate the total amount on the backend
        product_list = []
        first_vendor = None
        for item in cart_data: 
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)  # Default to 1 if quantity is not provided

            logger.info(f'Processing item: {item}')

            if not product_id:
                return Response({'error': 'Missing product ID in cart item.'}, status=status.HTTP_400_BAD_REQUEST)

            product = get_object_or_404(Product, id=product_id)

            if not first_vendor:
                first_vendor = product.vendor

            # Safely convert product price to Decimal and log it
            try:
                product_price = Decimal(str(product.price))
                logger.info(f'Product price for {product.title}: {product_price}')
            except (ValueError, decimal.InvalidOperation):
                logger.error(f'Invalid product price format for product {product.title}.')
                return Response({'error': 'Invalid product price format.'}, status=status.HTTP_400_BAD_REQUEST)

            # Safely convert quantity to Decimal
            try:
                quantity_decimal = Decimal(str(quantity))
                logger.info(f'Quantity for {product.title}: {quantity_decimal}')
            except (ValueError, decimal.InvalidOperation):
                logger.error(f'Invalid quantity format for product {product.title}: {quantity}')
                return Response({'error': f'Invalid quantity format for product {product.title}.'}, status=status.HTTP_400_BAD_REQUEST)

            # Update total_amount with product price and quantity
            try:
                total_amount += product_price * quantity_decimal
                logger.info(f'Updated total_amount after adding {product.title}: {total_amount}')
            except decimal.InvalidOperation as e:
                logger.error(f'Error updating total_amount: {e}')
                return Response({'error': 'Error calculating total amount.'}, status=status.HTTP_400_BAD_REQUEST)

            product_list.append({
                'title': product.title,
                'price': str(product.price),
                'image': product.image.url
            })

        # Validate coupon code if provided
        discount_amount = Decimal(0)
        if coupon_code:
            valid_coupons = Coupon.objects.filter(code=coupon_code, product__in=[item.get('product_id') for item in cart_data], is_active=True)
            if valid_coupons.exists():
                for coupon in valid_coupons:
                    # Apply coupon to specific product(s)
                    discount_amount += coupon.discount_amount
                total_amount -= discount_amount
                logger.info(f'Discount applied: {discount_amount}, new total_amount: {total_amount}')
            else:
                return Response({'error': 'Invalid or expired coupon code.'}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure total_amount is non-negative
        try:
            logger.info(f'Before checking, total_amount: {total_amount}')
            if total_amount < 0:
                total_amount = Decimal(0)
                logger.info('Total amount set to 0 due to negative value.')
        except decimal.InvalidOperation as e:
            logger.error(f'Error comparing total_amount to 0: {e}, total_amount: {total_amount}')
            return Response({'error': 'Error comparing total amount.'}, status=status.HTTP_400_BAD_REQUEST)

        # Set order status based on payment method
        order_status = 'Confirm' if payment_method == 'mobile-banking' else 'Pending'

        # Create the Order and associate it with the first vendor
        order = Order.objects.create(
            customer=customer,
            vendor=first_vendor,
            total_amount=total_amount,
            discount_price=discount_price,
            order_status=order_status,
            payment_method=payment_method,
            select_courier=select_courier,
        )

        # Create OrderItems for each product in the cart
        for item in cart_data:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)  # Use get to avoid KeyError
            product = get_object_or_404(Product, id=product_id)

            OrderItems.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )

        # Send confirmation email
        customer_email = customer.user.email
        vendor = first_vendor.user
        vendor_first_name = vendor.first_name
        vendor_last_name = vendor.last_name
        vendor_email = vendor.email
        vendor_phone = first_vendor.phone
        vendor_shop_name = first_vendor.shop_name
        # Email subject
        subject = 'Thank You for Your Purchase! Order Confirmation'

        # Prepare email context
        context = {
            'customer_first_name': customer.user.first_name,
            'customer_last_name': customer.user.last_name,
            'order_number': order.id,
            'order_date': order.order_time,
            'product_list': product_list,
            'discount_amount': str(discount_amount),
            'total_amount': str(total_amount),
            'payment_method': payment_method,
            'select_courier': select_courier,
            'vendor_shop_name': vendor_shop_name,

            'vendor_first_name': vendor_first_name,
            'vendor_last_name': vendor_last_name,
            'vendor_email': vendor_email,
            'vendor_phone': vendor_phone,
        }

        html_message = render_to_string('order_confirmation_email.html', context)
        plain_message = strip_tags(html_message)

        send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [customer_email], html_message=html_message)

        SentEmail.objects.create(
            recipient=customer_email,
            subject=subject,
            message=plain_message,
            customer=customer.user,
            vendor=vendor
        )

        order_serializer = OrderSerializer(order)
        return Response(order_serializer.data, status=status.HTTP_201_CREATED)



#### Order Items

class OrderItemsList(generics.ListCreateAPIView):
    queryset = OrderItems.objects.all().order_by('-id')
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
    queryset = OrderItems.objects.all().order_by('-id')
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        customer_id = self.kwargs['pk']
        qs = qs.filter(order__customer__id=customer_id)
        return qs


#Vendor order item list
class VendorOrderItemsList(generics.ListAPIView):
    queryset = OrderItems.objects.all().order_by('-id')
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        vendor_id = self.kwargs['pk']
        qs = qs.filter(product__vendor__id=vendor_id)
        return qs
    



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
    


class OrderItemDetailS(generics.RetrieveUpdateDestroyAPIView):
    queryset = OrderItems.objects.all()
    serializer_class = OrderItemSerializer



class OrderModify(generics.RetrieveUpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)  # Allow partial updates
        instance = self.get_object()  # Get the current order instance
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid():
            # Get the old status and the new status
            old_status = instance.order_status
            new_status = serializer.validated_data.get('order_status', old_status)

            # Update the order instance
            self.perform_update(serializer)

            # Prepare email details if the status has changed
            if old_status != new_status:
                subject = ''
                html_message = ''
                context = {
                    'customer_name': f'{instance.customer.user.first_name} {instance.customer.user.last_name}',
                    'order_number': instance.id,
                    'vendor_name': instance.vendor.user.username,
                    'vendor_email': instance.vendor.user.email,
                    'vendor_phone': instance.vendor.phone,
                    'order_date': instance.order_time.strftime('%Y-%m-%d %H:%M:%S'),  # Format as needed
                    # Add any other context variables needed for your templates
                }

                if new_status == 'Confirm':
                    subject = 'Order Confirmation'
                    html_message = render_to_string('order_confirmation_email.html', context)
                elif new_status == 'Delivered':
                    subject = 'Order Delivered'
                    html_message = render_to_string('order_delivered_email.html', context)
                elif new_status == 'Cancelled':
                    subject = 'Order Cancelled'
                    html_message = render_to_string('order_cancelled_email.html', context)

                # Send the email
                send_mail(
                    subject,
                    message='',  # No plain text message
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.customer.user.email],
                    html_message=html_message,
                    fail_silently=False,
                )

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



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
    authentication_classes = ([JWTAuthentication,TokenAuthentication])
    permission_classes = [IsAuthenticated]

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


@api_view(['GET'])
def check_default_address(request):
    try:
        # Check if the user has a related Customer object
        customer = request.user.customer
        
        # Check if the customer has a default address
        default_address = CustomerAddress.objects.filter(customer=customer, default_address=True).first()
        
        if default_address:
            return JsonResponse({'default_address': True, 'address': default_address.address})
        else:
            return JsonResponse({'default_address': False, 'message': 'No default address found'})
    
    except Customer.DoesNotExist:
        # Handle the case where the user has no associated customer
        return JsonResponse({'error': 'User has no customer'}, status=400)



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



        


class ProductRatingViewSet(viewsets.ModelViewSet):
    serializer_class = ProductReviewSerializer
    queryset = ProductRating.objects.all()





################### product Category ###################

class CategoryList(generics.ListAPIView):
    queryset = ProductCategory.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if 'category_fetch_limit' in self.request.GET:
            limit = self.request.GET['category_fetch_limit']
            qs = qs.annotate(downloads=Count('category_product'))
            qs = qs[:int(limit)]
        return qs
    


class AddCategory(generics.ListCreateAPIView):
    queryset = ProductCategory.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated,IsAdminUser]


class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductCategory.objects.all()
    serializer_class = CategoryDetailSerializer




@csrf_exempt
def Update_Order_Status(request, pk):
    order_id = pk
    if request.method == "POST":
        try:
            # Update the order status to "True" or a specific status, like "COMPLETED"
            update_order_status = Order.objects.filter(id=order_id).update(order_status=True)
            msg = {'bool': False}
            
            if update_order_status:
                msg = {'bool': True}
                
            return JsonResponse(msg)
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)
    


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

@permission_classes([AllowAny])
@api_view(['POST'])
def initiate_payment(request):
    post_data = request.data
    order_id = post_data.get('order_id')

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({"error": "Order does not exist"}, status=400)

    amount_str = post_data.get('amount')

    # Validate and convert amount
    try:
        total_amount = Decimal(amount_str).quantize(Decimal('0.01'))
        print(f"Received amount: {amount_str}")
        if total_amount <= 0:
            return Response({"error": "Amount must be greater than zero"}, status=400)
    except (ValueError, InvalidOperation):
        return Response({"error": f"Invalid amount format: {amount_str}"}, status=400)


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
        order=order,
    )

    # Prepare payment data using SSLCommerz API
    payment_data = {
        'store_id': 'kopot665596f0af929',
        'store_passwd': 'kopot665596f0af929@ssl',
        'total_amount': transaction.amount,
        'currency': transaction.currency,
        'tran_id': transaction.transaction_id,
        'product_name': 'Order Items',
        'product_category': 'Various',
        'product_profile': 'General',
        'success_url': f'{base_url}/api/payment-success/',
        'fail_url': f'{base_url}/api/payment-fail/',
        'cancel_url': f'{base_url}/api/payment-cancel/',
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

    # Call SSLCommerz payment API
    response = requests.post('https://sandbox.sslcommerz.com/gwprocess/v4/api.php', data=payment_data)
    return Response(response.json())


@api_view(['POST'])
@permission_classes([AllowAny])
def payment_success(request):
    post_data = request.POST
    transaction_id = post_data.get('tran_id')  # Get the transaction ID

    # Log post_data to see if SSLCommerz sent it correctly
    print(f"POST data received in payment_success: {post_data}")

    try:
        # Fetch the transaction
        transaction = Transaction.objects.get(transaction_id=transaction_id)
        
        # Update transaction status to success
        transaction.status = 'SUCCESS'
        transaction.save()

        # Redirect to frontend
        client_site_url = f'http://localhost:3000/order-success/'
        return redirect(client_site_url)
    except Transaction.DoesNotExist:
        return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)



@api_view(['POST'])
@permission_classes([AllowAny])
def payment_fail(request):
    post_data = request.POST
    transaction_id = post_data.get('tran_id')
    try:
        transaction = Transaction.objects.get(transaction_id=transaction_id)
        transaction.status = 'FAILED'
        transaction.save()
        client_site_url = f'http://localhost:3000/'
        return redirect(client_site_url)
    except Transaction.DoesNotExist:
        return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)


@permission_classes([AllowAny])
@api_view(['POST'])
def payment_cancel(request):
    post_data = request.POST
    transaction_id = post_data.get('tran_id')
    try:
        transaction = Transaction.objects.get(transaction_id=transaction_id)
        transaction.status = 'CANCELLED'
        transaction.save()
        return Response({'status': 'cancelled'})
    except Transaction.DoesNotExist:
        return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)
    




class SuperuserLoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        user = self.get_user_from_request(request)
        
        if not user.is_superuser:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        return response

    def get_user_from_request(self, request):
        # Extract the user from the request's validated token
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.user
        
        

def admin_dashboard(request):
    totalVendors = Vendor.objects.all().count()
    totalCustomers = Customer.objects.all().count()
    # totalCustomers = OrderItems.objects.filter(product__vendor__id=vendor_id).values('order__customer').count()
    totalOrders = OrderItems.objects.all().distinct().count()
    
    context = {
        'totalOrders': totalOrders,
        'totalCustomers': totalCustomers,
        'totalVendors': totalVendors,
    }
    return JsonResponse(context)



@api_view(['DELETE'])
# @permission_classes(IsAdminUser)
def delete_vendor(request, pk):
    try:
        vendor = Vendor.objects.get(pk=pk)
    except Vendor.DoesNotExist:
        return Response({'detail': 'Vendor not found.'}, status=status.HTTP_404_NOT_FOUND)

    vendor.delete()
    return Response({'detail': 'Vendor deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)



class OrderListForAdminView(generics.ListAPIView):
    queryset = Order.objects.all().order_by('-id')
    serializer_class = OrderSerializer
    pagination_class = CustomPagination
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]




class CustomerOrderItemListShowForAdmin(generics.ListAPIView):
    queryset = OrderItems.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        customer_id = self.kwargs['customer_id']
        qs = qs.filter(order__customer__id=customer_id)
        return qs
    



class VendorOrderedProductsListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        vendor_id = self.kwargs['vendor_id']
        
        # Get all products for the vendor
        products = Product.objects.filter(vendor_id=vendor_id).order_by('-id')
        
        # Subquery to count confirmed orders for each product
        confirmed_orders_subquery = OrderItems.objects.filter(
            product=OuterRef('pk'),
            order__order_status='Confirm'
        ).values('product').annotate(order_count=Count('id')).values('order_count')
        
        # Annotate products with the count of confirmed orders
        products_with_counts = products.annotate(
            order_count=Subquery(confirmed_orders_subquery)
        )
        
        return products_with_counts
    


#For admin search
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_orders_by_date(request):
    # Get the date parameter from the query string
    order_date = request.query_params.get('date', None)
    
    if order_date:
        # Parse the date and filter orders by the date
        order_date_parsed = parse_date(order_date)
        orders = Order.objects.filter(order_time__date=order_date_parsed).order_by('-id')
        
        # Serialize the orders
        serializer = OrderSerializer(orders, many=True)
        return Response({'data': serializer.data}, status=200)
    
    return Response({'error': 'Invalid date'}, status=400)



#For vendor search
class VendorOrderSearchView(APIView):
    def get(self, request, vendor_id):
        # Get the 'id' from query parameters for searching
        order_id = request.query_params.get('id', None)

        if order_id:
            try:
                # Filter the orders by the provided 'id' and vendor_id
                order = Order.objects.filter(id=order_id, vendor_id=vendor_id).first()
                
                if not order:
                    return Response({'detail': 'Order not found'}, status=404)

            except ValueError:
                return Response({'detail': 'Invalid order ID'}, status=400)
            
            # Serialize the single order
            serializer = OrderSerializer(order)
            return Response({'data': [serializer.data]}, status=200)  # Return a list with the matching order
        
        else:
            # If no 'id' is provided, return all orders for the vendor
            orders = Order.objects.filter(vendor_id=vendor_id)
            serializer = OrderSerializer(orders, many=True)
            return Response({'data': serializer.data}, status=200)




class VendorDateWiseOrderSearch(APIView):
    def get(self, request, vendor_id, *args, **kwargs):
        selected_date = request.GET.get('date')
        if selected_date:
            try:
                # Convert string to date object
                selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Invalid date format"}, status=400)
            
            # Filter orders by the selected date and vendor
            order_items = OrderItems.objects.filter(order__vendor_id=vendor_id, order__order_time__date=selected_date_obj)
        else:
            # Handle case where no date is provided, fetch all orders for the vendor
            order_items = OrderItems.objects.filter(order__vendor_id=vendor_id)
        
        # Serialize and return the data
        serializer = OrderItemSerializer(order_items, many=True)
        return Response({"data": serializer.data})
    


ORDER_STATUS = (
    ('Confirm', 'Confirm'),
    ('Delivered', 'Delivered'),
    ('Cancelled', 'Cancelled'),
)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def change_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = request.data.get('order_status')

    # Validate the new status
    if new_status not in dict(ORDER_STATUS):
        return Response({'error': 'Invalid status'}, status=400)

    # Update order status
    order.order_status = new_status
    order.save()

    # Prepare email details
    subject = ""
    html_message = ""
    context = {
        'customer_name': order.customer.first_name + " " + order.customer.last_name,
        'order_number': order.id,
        'payment_method': order.payment_method,  # Adjust as necessary
        'shop_name': "Your Shop Name",  # Replace with your shop name variable
        'product_list': order.order_items.all(),  # Adjust to get the list of products
        'vendor_name': order.vendor.username,
        'vendor_email': order.vendor.email,
        'vendor_phone': order.vendor.phone,
        'order_date': order.order_time,  # Adjust to your order date field
    }

    if new_status == 'Confirm':
        subject = 'Order Confirmation'
        html_message = render_to_string('order_confirmation_email.html', context)
    elif new_status == 'Delivered':
        subject = 'Order Delivered'
        html_message = render_to_string('order_delivered_email.html', context)
    elif new_status == 'Cancelled':
        subject = 'Order Cancelled'
        html_message = render_to_string('order_cancelled_email.html', context)

    if subject and html_message:
        # Send the email
        send_mail(
            subject,
            strip_tags(html_message),  # Text version of the email
            settings.DEFAULT_FROM_EMAIL,
            [order.customer.email],
            html_message=html_message,
            fail_silently=False,
        )

        # Save the email details to the SentEmail model
        SentEmail.objects.create(
            recipient=order.customer.email,
            subject=subject,
            message=html_message,
            customer=order.customer,
            vendor=order.vendor,  # Assuming `order` has a vendor field
        )

    return Response({'status': 'success', 'message': f'Order status changed to {new_status} and email sent.'})