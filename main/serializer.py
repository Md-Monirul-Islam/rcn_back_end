from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Product, ProductCategory, ProductImage, Vendor,Customer,Order,OrderItems,CustomerAddress, ProductRating, WishList

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
        fields = ['id','category','vendor','title','slug','tag_list','detail','price','usd_price','product_ratings','image','product_file','downloads']

        def __init__(self,*args, **kwargs):
            super(ProductListSerializer,self).__init__(*args, **kwargs)
        # depth = 1



class ProductDetailSerializer(serializers.ModelSerializer):
    product_ratings = serializers.StringRelatedField(many=True, read_only=True)
    product_image = serializers.StringRelatedField(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ['id','category','vendor','title','slug','tag_list','detail','price','usd_price','product_ratings','product_image','demo_url','image','product_file','downloads']

        def __intit__(self,*args, **kwargs):
            super(ProductDetailSerializer,self).__init__(*args, **kwargs)
        # depth = 1



class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id','product','image']

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Customer
        fields = ['user', 'profile_image', 'phone']
        
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user')
        user = instance.user

        instance.profile_image = validated_data.get('profile_image', instance.profile_image)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.save()

        user_serializer = UserSerializer(instance=user, data=user_data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()

        return instance
        
    
    # depth = 1


class OrderSerializer(serializers.ModelSerializer):
    # customer = CustomerSerializer()
    class Meta:
        model = Order
        fields = '__all__'
        # depth = 1


class OrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItems
        fields = ['id','order','product']
        # depth = 1



class OrderItemSerializer(serializers.ModelSerializer):
    # order = OrderSerializer()
    # product = ProductDetailSerializer()
    class Meta:
        model = OrderItems
        fields = '__all__'
        # depth = 1

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['order'] = OrderSerializer(instance.order, context=self.context).data
        response['product'] = ProductDetailSerializer(instance.product, context=self.context).data
        return response


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


class WishListSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishList
        fields = '__all__'
        # depth = 1
    
    def __init__(self,*args, **kwargs):
        super(WishListSerializer,self).__init__(*args, **kwargs)

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['customer'] = CustomerSerializer(instance.customer, context=self.context).data
        response['product'] = ProductDetailSerializer(instance.product, context=self.context).data
        return response