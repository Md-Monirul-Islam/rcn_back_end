from rest_framework import serializers
from .models import Product, ProductCategory, ProductImage, Vendor,Customer,Order,OrderItems,CustomerAddress, ProductRating

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'user', 'address']
        # depth = 1

class VendorDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'user', 'address']
        # depth = 1


class ProductListSerializer(serializers.ModelSerializer):
    product_ratings = serializers.StringRelatedField(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ['id','category','vendor','title','slug','tag_list','detail','price','product_ratings']
        # depth = 1



class ProductDetailSerializer(serializers.ModelSerializer):
    product_ratings = serializers.StringRelatedField(many=True, read_only=True)
    product_image = serializers.StringRelatedField(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ['id','category','vendor','title','slug','tag_list','detail','price','product_ratings','product_image']
        # depth = 1



class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id','product','image']



class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        depth = 1


class OrderSerializer(serializers.ModelSerializer):
    # customer = CustomerSerializer()
    class Meta:
        model = Order
        fields = '__all__'
        # depth = 1


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItems
        fields = '__all__'
        # depth = 1


class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = '__all__'
        depth = 1



class ProiductReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductRating
        fields = '__all__'
        depth = 1



################### Category ###################

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = '__all__'
        depth = 1



class CategoryDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = '__all__'
        depth = 1