import datetime
from rest_framework import serializers, generics
from django.contrib.auth.models import User
from .models import Product, ProductCategory, ProductImage, Transaction, Vendor,Customer,Order,OrderItems,CustomerAddress, ProductRating, WishList

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'user', 'address']
        depth = 1

class VendorDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'user', 'address']
        # depth = 1


class ProductListSerializer(serializers.ModelSerializer):
    product_ratings = serializers.StringRelatedField(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ['id','category','vendor','title','slug','tags','detail','price','usd_price','demo_url','product_ratings','image','product_file','downloads','publish_status','product_image']

        def __init__(self,*args, **kwargs):
            super(ProductListSerializer,self).__init__(*args, **kwargs)
        # depth = 1


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id','product','image']



class ProductDetailSerializer(serializers.ModelSerializer):
    product_ratings = serializers.StringRelatedField(many=True, read_only=True)
    product_image = ProductImageSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ['id','category','vendor','title','slug','tags','detail','price','usd_price','product_ratings','product_image','demo_url','image','product_file','downloads','publish_status']

        def __intit__(self,*args, **kwargs):
            super(ProductDetailSerializer,self).__init__(*args, **kwargs)
        # depth = 1





class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'password']

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'password']

class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Customer
        fields = ['id', 'user', 'profile_image', 'phone']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user_instance = instance.user
            for attr, value in user_data.items():
                setattr(user_instance, attr, value)
            user_instance.save()

        instance.profile_image = validated_data.get('profile_image', instance.profile_image)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.save()

        return instance

class CustomerDetails(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
        
    
    # depth = 1


class OrderSerializer(serializers.ModelSerializer):
    # customer = CustomerSerializer()
    class Meta:
        model = Order
        fields = '__all__'
        # depth = 1
        # def __init__(self,*args, **kwargs):
        #     super(OrderSerializer,self).__init__(*args, **kwargs)
        #     self.Meta.depth=1

    def to_representation(self, instance):
        response = super().to_representation(instance)
        # Add customer details from the related User model
        response['customer'] = {
            'customer_id': instance.customer.user.id,
            'first_name': instance.customer.user.first_name,
            'last_name': instance.customer.user.last_name,
            'email': instance.customer.user.email,
            'phone': instance.customer.phone,
        }
        return response


class OrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItems
        fields = ['id','order','product']
        # depth = 1



class OrderItemSerializer(serializers.ModelSerializer):
    # order = OrderSerializer()
    # product = ProductDetailSerializer()
    # order_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = OrderItems
        fields = '__all__'
        # fields = ['order', 'product', 'quantity', 'price', 'order_count']
        # depth = 1

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['order'] = OrderSerializer(instance.order, context=self.context).data
        response['product'] = ProductDetailSerializer(instance.product, context=self.context).data

        return response
    


class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = ['id','customer','address','city','post','default_address']
        
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['customer'] = CustomerSerializer(instance.customer, context=self.context).data
        return response



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
    


    class TransactionSerializer(serializers.ModelSerializer):
        class Meta:
            model = Transaction,
            fields = '__all__',


#Vendor report serializer
# class VendorDailyReportSerializer(serializers.Serializer):
#     order_date = serializers.DateField(source='order__order_time__date')
#     total_orders = serializers.IntegerField()



# class VendorDailyReportSerializer(serializers.Serializer):
#     date = serializers.DateField(required=False)
#     month = serializers.DateField(required=False)
#     year = serializers.DateField(required=False)
#     total_orders = serializers.IntegerField()


#date,month and year wise
class VendorDailyReportSerializer(serializers.Serializer):
    date = serializers.DateField(required=False, allow_null=True)
    month = serializers.DateField(required=False, allow_null=True)
    year = serializers.DateField(required=False, allow_null=True)
    total_orders = serializers.IntegerField()

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        # Clean up empty fields
        if not ret.get('date'):
            ret.pop('date', None)
        if not ret.get('month'):
            ret.pop('month', None)
        if not ret.get('year'):
            ret.pop('year', None)

        return ret