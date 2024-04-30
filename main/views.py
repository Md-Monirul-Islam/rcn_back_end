from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import generics,permissions,viewsets
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