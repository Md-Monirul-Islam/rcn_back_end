from django.shortcuts import render
from rest_framework import generics,permissions,viewsets
from .models import *
from .serializer import *

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



class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer



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